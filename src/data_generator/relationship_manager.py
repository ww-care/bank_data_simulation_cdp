#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
关系管理模块

负责管理实体间的关系，如客户与经理的分配关系等。
"""

import random
import datetime
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import defaultdict

from src.logger import get_logger
from src.database_manager import get_database_manager


class ManagerClientAssignment:
    """
    银行经理与客户分配关系管理类
    
    负责客户与经理的分配，包括VIP客户特别处理、负载均衡等功能。
    """
    
    def __init__(self, managers: List[Dict], customers: List[Dict]):
        """
        初始化客户经理分配器
        
        Args:
            managers: 经理数据列表
            customers: 客户数据列表
        """
        self.managers = managers
        self.customers = customers
        
        # 初始化日志
        self.logger = get_logger('ManagerClientAssignment')
        
        # 客户经理分配映射 {manager_id: [customer_id1, customer_id2, ...]}
        self.assignments = {}
        
        # 初始化分配映射
        for manager in self.managers:
            self.assignments[manager['base_id']] = []
        
        # 分配容量配置，可根据需要调整
        self.capacity_config = {
            '初级客户经理': {
                'regular': 100,  # 普通客户最大数量
                'vip': 15,       # VIP客户最大数量
                'total': 100     # 总客户最大数量
            },
            '高级客户经理': {
                'regular': 120,
                'vip': 30,
                'total': 150
            },
            '资深客户经理': {
                'regular': 150,
                'vip': 50,
                'total': 200
            },
            '客户经理主管': {
                'regular': 80,
                'vip': 40,
                'total': 120
            },
            '业务主管': {
                'regular': 50,
                'vip': 30,
                'total': 80
            },
            '部门经理': {
                'regular': 20,
                'vip': 20,
                'total': 40
            }
        }
        
        # 初始化客户位置缓存 {location: [customers]}
        self.customers_by_location = {}
        
        # 初始化经理位置缓存 {location: [managers]}
        self.managers_by_location = {}
        
        # 初始化已分配的客户集合
        self.assigned_customers = set()
    
    def assign_clients(self) -> Dict[str, List[str]]:
        """
        执行客户分配，遵循以下规则：
        1. VIP客户优先分配给高级及以上经理
        2. 考虑地理位置就近原则
        3. 考虑经理的客户容量限制
        4. 负载均衡，避免某些经理分配过多客户
        
        Returns:
            经理ID到客户ID列表的映射
        """
        self.logger.info("开始执行客户经理分配")
        
        # 创建客户和经理的地理位置索引
        self._group_by_location()
        
        # 分配VIP客户
        self._assign_vip_clients()
        
        # 分配普通客户
        self._assign_regular_clients()
        
        # 平衡经理的工作负载
        self._balance_workload()
        
        # 更新经理的客户数量字段
        self._update_manager_client_counts()
        
        # 输出分配统计信息
        self._log_assignment_statistics()
        
        self.logger.info("客户经理分配完成")
        
        return self.assignments
    
    def _group_by_location(self):
        """
        按地理位置分组客户和经理，用于就近分配
        """
        # 客户按地理位置分组
        self.customers_by_location = defaultdict(list)
        for customer in self.customers:
            location = self._extract_location(customer)
            self.customers_by_location[location].append(customer)
        
        # 经理按地理位置分组
        self.managers_by_location = defaultdict(list)
        for manager in self.managers:
            location = self._extract_location(manager)
            self.managers_by_location[location].append(manager)
        
        self.logger.info(f"按地理位置分组: {len(self.customers_by_location)} 个客户地区, {len(self.managers_by_location)} 个经理地区")
    
    def _extract_location(self, entity: Dict) -> str:
        """
        从实体中提取位置信息
        
        Args:
            entity: 实体数据（客户或经理）
            
        Returns:
            位置标识（省份+城市）
        """
        # 优先使用省份+城市组合作为位置标识
        province = entity.get('province', '')
        city = entity.get('city', '')
        
        if province and city:
            return f"{province}_{city}"
        elif city:
            return city
        elif province:
            return province
        
        # 如果没有明确的位置信息，尝试从地址中提取
        address = entity.get('address', '')
        if address:
            # 简单的地址解析，实际可能需要更复杂的地址解析逻辑
            for city_name in ['北京', '上海', '广州', '深圳', '天津', '重庆', '杭州', '南京', '武汉', '成都', '西安']:
                if city_name in address:
                    return city_name
        
        # 没有位置信息时返回默认值
        return "未知"
    
    def _assign_vip_clients(self):
        """
        分配VIP客户，优先分配给高级及以上经理，考虑地理位置就近原则
        """
        # 获取所有VIP客户
        vip_customers = [c for c in self.customers if c.get('is_vip', False)]
        self.logger.info(f"开始分配 {len(vip_customers)} 个VIP客户")
        
        # 筛选高级及以上经理（高级客户经理、资深客户经理、客户经理主管、业务主管、部门经理）
        senior_positions = ['高级客户经理', '资深客户经理', '客户经理主管', '业务主管', '部门经理']
        senior_managers = [m for m in self.managers if m.get('position') in senior_positions]
        
        if not senior_managers:
            self.logger.warning("没有高级经理可用，将使用所有经理分配VIP客户")
            senior_managers = self.managers
        
        # 按地区分组VIP客户
        vip_by_location = defaultdict(list)
        for customer in vip_customers:
            location = self._extract_location(customer)
            vip_by_location[location].append(customer)
        
        # 第一轮：按地域就近原则分配
        for location, location_customers in vip_by_location.items():
            # 检查该地区是否有高级经理
            location_managers = [m for m in senior_managers if self._extract_location(m) == location]
            
            if not location_managers:
                # 如果该地区没有高级经理，跳过，留待后续处理
                continue
            
            # 为该地区的每个VIP客户找到合适的经理
            for customer in location_customers:
                if customer['base_id'] in self.assigned_customers:
                    continue
                
                # 检查经理是否已达到VIP客户上限
                eligible_managers = [m for m in location_managers if 
                                    self._count_vip_clients(m['base_id']) < self._get_vip_capacity(m)]
                
                if not eligible_managers:
                    # 如果该地区所有经理都已达VIP上限，跳过，留待后续处理
                    continue
                
                # 找出客户最少的经理进行分配
                manager = min(eligible_managers, key=lambda m: len(self.assignments[m['base_id']]))
                
                # 分配客户给经理
                self.assignments[manager['base_id']].append(customer['base_id'])
                self.assigned_customers.add(customer['base_id'])
        
        # 第二轮：为未分配的VIP客户找经理（不考虑地域）
        unassigned_vips = [c for c in vip_customers if c['base_id'] not in self.assigned_customers]
        
        for customer in unassigned_vips:
            # 找出VIP客户数未达上限的经理
            eligible_managers = [m for m in senior_managers if 
                                self._count_vip_clients(m['base_id']) < self._get_vip_capacity(m)]
            
            if not eligible_managers:
                # 如果所有高级经理都已达VIP上限，转向所有经理
                eligible_managers = [m for m in self.managers if 
                                     self._count_vip_clients(m['base_id']) < self._get_vip_capacity(m)]
            
            if eligible_managers:
                # 找出客户最少的经理进行分配
                manager = min(eligible_managers, key=lambda m: len(self.assignments[m['base_id']]))
                
                # 分配客户给经理
                self.assignments[manager['base_id']].append(customer['base_id'])
                self.assigned_customers.add(customer['base_id'])
            else:
                # 所有经理都达到了VIP上限，记录警告
                self.logger.warning(f"无法为VIP客户 {customer['base_id']} 分配经理，所有经理都已达到VIP客户上限")
        
        # 统计分配结果
        assigned_vip_count = sum(1 for c in vip_customers if c['base_id'] in self.assigned_customers)
        self.logger.info(f"已完成 {assigned_vip_count}/{len(vip_customers)} 个VIP客户分配")
    
    def _assign_regular_clients(self):
        """
        分配普通客户，考虑地理位置就近原则和负载均衡
        """
        # 获取所有普通客户（非VIP）
        regular_customers = [c for c in self.customers if not c.get('is_vip', False)]
        self.logger.info(f"开始分配 {len(regular_customers)} 个普通客户")
        
        # 按地区分组普通客户
        regular_by_location = defaultdict(list)
        for customer in regular_customers:
            location = self._extract_location(customer)
            regular_by_location[location].append(customer)
        
        # 第一轮：按地域就近原则分配
        for location, location_customers in regular_by_location.items():
            # 获取该地区的经理
            location_managers = [m for m in self.managers if self._extract_location(m) == location]
            
            if not location_managers:
                # 如果该地区没有经理，跳过，留待后续处理
                continue
            
            # 为该地区的每个普通客户找到合适的经理
            for customer in location_customers:
                if customer['base_id'] in self.assigned_customers:
                    continue
                
                # 检查经理是否已达到普通客户上限或总客户上限
                eligible_managers = [m for m in location_managers if 
                                     self._count_regular_clients(m['base_id']) < self._get_regular_capacity(m) and
                                     len(self.assignments[m['base_id']]) < self._get_total_capacity(m)]
                
                if not eligible_managers:
                    # 如果该地区所有经理都已达上限，跳过，留待后续处理
                    continue
                
                # 找出客户最少的经理进行分配
                manager = min(eligible_managers, key=lambda m: len(self.assignments[m['base_id']]))
                
                # 分配客户给经理
                self.assignments[manager['base_id']].append(customer['base_id'])
                self.assigned_customers.add(customer['base_id'])
        
        # 第二轮：为未分配的普通客户找经理（不考虑地域）
        unassigned_regulars = [c for c in regular_customers if c['base_id'] not in self.assigned_customers]
        
        for customer in unassigned_regulars:
            # 找出普通客户数和总客户数未达上限的经理
            eligible_managers = [m for m in self.managers if 
                                 self._count_regular_clients(m['base_id']) < self._get_regular_capacity(m) and
                                 len(self.assignments[m['base_id']]) < self._get_total_capacity(m)]
            
            if eligible_managers:
                # 找出客户最少的经理进行分配
                manager = min(eligible_managers, key=lambda m: len(self.assignments[m['base_id']]))
                
                # 分配客户给经理
                self.assignments[manager['base_id']].append(customer['base_id'])
                self.assigned_customers.add(customer['base_id'])
            else:
                # 所有经理都达到了上限，记录警告
                self.logger.warning(f"无法为普通客户 {customer['base_id']} 分配经理，所有经理都已达到客户容量上限")
        
        # 统计分配结果
        assigned_regular_count = sum(1 for c in regular_customers if c['base_id'] in self.assigned_customers)
        self.logger.info(f"已完成 {assigned_regular_count}/{len(regular_customers)} 个普通客户分配")
    
    def _balance_workload(self):
        """
        平衡各经理的工作负载，重新分配超载经理的客户
        """
        # 检查是否有超载的经理（客户数量超过总容量）
        overloaded_managers = []
        for manager in self.managers:
            manager_id = manager['base_id']
            assigned_count = len(self.assignments[manager_id])
            total_capacity = self._get_total_capacity(manager)
            
            if assigned_count > total_capacity:
                overload_amount = assigned_count - total_capacity
                overloaded_managers.append((manager, overload_amount))
        
        if not overloaded_managers:
            self.logger.info("所有经理的工作负载均在容量范围内，无需重新平衡")
            return
        
        # 按超载数量排序，超载最严重的优先处理
        overloaded_managers.sort(key=lambda x: x[1], reverse=True)
        
        self.logger.info(f"发现 {len(overloaded_managers)} 个超载经理，开始重新分配客户")
        
        for manager, overload_amount in overloaded_managers:
            manager_id = manager['base_id']
            
            # 获取该经理的客户列表
            manager_customers = self.assignments[manager_id]
            
            # 找出可以接收更多客户的经理
            underloaded_managers = [m for m in self.managers if 
                                   m['base_id'] != manager_id and 
                                   len(self.assignments[m['base_id']]) < self._get_total_capacity(m)]
            
            if not underloaded_managers:
                self.logger.warning(f"无法重新分配经理 {manager_id} 的客户，所有其他经理都已满载")
                continue
            
            # 计算需要重新分配的客户数量
            num_to_reassign = min(overload_amount, len(manager_customers))
            
            # 优先重新分配普通客户，保留VIP客户
            vip_customer_ids = self._get_vip_customer_ids(manager_customers)
            regular_customer_ids = [cid for cid in manager_customers if cid not in vip_customer_ids]
            
            # 确定要重新分配的客户ID
            to_reassign = []
            if len(regular_customer_ids) >= num_to_reassign:
                # 如果普通客户足够，只重新分配普通客户
                to_reassign = regular_customer_ids[:num_to_reassign]
            else:
                # 如果普通客户不够，也需要重新分配部分VIP客户
                to_reassign = regular_customer_ids + vip_customer_ids[:num_to_reassign - len(regular_customer_ids)]
            
            # 从当前经理移除这些客户
            for customer_id in to_reassign:
                self.assignments[manager_id].remove(customer_id)
            
            # 重新分配这些客户
            for customer_id in to_reassign:
                # 确定客户类型
                is_vip = customer_id in vip_customer_ids
                
                # 筛选可接收此类客户的经理
                eligible_managers = []
                for m in underloaded_managers:
                    if is_vip:
                        if self._count_vip_clients(m['base_id']) < self._get_vip_capacity(m):
                            eligible_managers.append(m)
                    else:
                        if self._count_regular_clients(m['base_id']) < self._get_regular_capacity(m):
                            eligible_managers.append(m)
                
                if not eligible_managers:
                    # 如果没有合适的经理，放回原经理
                    self.assignments[manager_id].append(customer_id)
                    continue
                
                # 找出客户最少的经理进行分配
                target_manager = min(eligible_managers, key=lambda m: len(self.assignments[m['base_id']]))
                
                # 分配客户给经理
                self.assignments[target_manager['base_id']].append(customer_id)
                
                # 更新未满载经理列表
                if len(self.assignments[target_manager['base_id']]) >= self._get_total_capacity(target_manager):
                    underloaded_managers.remove(target_manager)
            
            self.logger.info(f"已从经理 {manager_id} 重新分配 {len(to_reassign)} 个客户")
    
    def _update_manager_client_counts(self):
        """
        更新经理的客户数量字段
        """
        for manager in self.managers:
            manager_id = manager['base_id']
            assigned_clients = self.assignments[manager_id]
            
            # 更新总客户数
            manager['current_client_count'] = len(assigned_clients)
            
            # 计算VIP客户数
            vip_count = self._count_vip_clients(manager_id)
            
            # 更新活跃客户数（根据一定规则计算，这里简化为总数的70-90%）
            active_ratio = 0.7 + (0.2 * (vip_count / max(len(assigned_clients), 1)))  # VIP占比越高，活跃率越高
            manager['active_client_count'] = int(len(assigned_clients) * active_ratio)
    
    def _log_assignment_statistics(self):
        """
        记录分配统计信息
        """
        # 客户分配率
        assigned_count = len(self.assigned_customers)
        total_count = len(self.customers)
        assignment_rate = (assigned_count / total_count) * 100 if total_count > 0 else 0
        
        # 经理负载情况
        manager_loads = [(m['base_id'], len(self.assignments[m['base_id']]), self._get_total_capacity(m)) 
                        for m in self.managers]
        avg_load = sum(load[1] for load in manager_loads) / len(manager_loads) if manager_loads else 0
        
        # 分职位统计
        position_stats = defaultdict(lambda: {'managers': 0, 'customers': 0, 'vip_customers': 0})
        for manager in self.managers:
            position = manager.get('position', '未知')
            manager_id = manager['base_id']
            position_stats[position]['managers'] += 1
            position_stats[position]['customers'] += len(self.assignments[manager_id])
            position_stats[position]['vip_customers'] += self._count_vip_clients(manager_id)
        
        # 记录统计结果
        self.logger.info(f"客户分配完成率: {assignment_rate:.2f}% ({assigned_count}/{total_count})")
        self.logger.info(f"平均每个经理分配客户数: {avg_load:.2f}")
        
        for position, stats in position_stats.items():
            avg_customers = stats['customers'] / stats['managers'] if stats['managers'] > 0 else 0
            avg_vip = stats['vip_customers'] / stats['managers'] if stats['managers'] > 0 else 0
            self.logger.info(f"{position}: {stats['managers']}人, 平均 {avg_customers:.2f} 客户/人, 平均 {avg_vip:.2f} VIP客户/人")
    
    def _count_vip_clients(self, manager_id: str) -> int:
        """
        计算经理的VIP客户数量
        
        Args:
            manager_id: 经理ID
            
        Returns:
            VIP客户数量
        """
        # 获取该经理的客户ID列表
        customer_ids = self.assignments[manager_id]
        
        # 统计VIP客户数量
        vip_count = 0
        for customer in self.customers:
            if customer['base_id'] in customer_ids and customer.get('is_vip', False):
                vip_count += 1
        
        return vip_count
    
    def _count_regular_clients(self, manager_id: str) -> int:
        """
        计算经理的普通客户数量
        
        Args:
            manager_id: 经理ID
            
        Returns:
            普通客户数量
        """
        # 总客户数减去VIP客户数
        return len(self.assignments[manager_id]) - self._count_vip_clients(manager_id)
    
    def _get_vip_capacity(self, manager: Dict) -> int:
        """
        获取经理的VIP客户容量
        
        Args:
            manager: 经理数据
            
        Returns:
            VIP客户容量
        """
        position = manager.get('position', '初级客户经理')
        return self.capacity_config.get(position, self.capacity_config['初级客户经理'])['vip']
    
    def _get_regular_capacity(self, manager: Dict) -> int:
        """
        获取经理的普通客户容量
        
        Args:
            manager: 经理数据
            
        Returns:
            普通客户容量
        """
        position = manager.get('position', '初级客户经理')
        return self.capacity_config.get(position, self.capacity_config['初级客户经理'])['regular']
    
    def _get_total_capacity(self, manager: Dict) -> int:
        """
        获取经理的总客户容量
        
        Args:
            manager: 经理数据
            
        Returns:
            总客户容量
        """
        position = manager.get('position', '初级客户经理')
        return self.capacity_config.get(position, self.capacity_config['初级客户经理'])['total']
    
    def _get_vip_customer_ids(self, customer_ids: List[str]) -> Set[str]:
        """
        获取VIP客户ID集合
        
        Args:
            customer_ids: 客户ID列表
            
        Returns:
            VIP客户ID集合
        """
        vip_ids = set()
        for customer in self.customers:
            if customer['base_id'] in customer_ids and customer.get('is_vip', False):
                vip_ids.add(customer['base_id'])
        return vip_ids
    
    def save_to_database(self) -> bool:
        """
        将分配结果保存到数据库，建立客户与经理的关联
        
        Returns:
            是否保存成功
        """
        try:
            # 获取数据库管理器实例
            from src.database_manager import get_database_manager
            db_manager = get_database_manager()
            
            # 构建关联数据
            associations = []
            for manager_id, customer_ids in self.assignments.items():
                for customer_id in customer_ids:
                    associations.append({
                        'manager_id': manager_id,
                        'customer_id': customer_id,
                        'assign_date': datetime.date.today().strftime('%Y-%m-%d'),
                        'status': 'active'
                    })
            
            if not associations:
                self.logger.warning("没有分配关系需要保存")
                return True
            
            # 转换为DataFrame
            import pandas as pd
            df = pd.DataFrame(associations)
            
            # 保存到数据库
            result = db_manager.import_dataframe('cdp_manager_customer_relation', df)
            
            if result > 0:
                self.logger.info(f"成功保存 {result} 条客户经理分配关系到数据库")
                return True
            else:
                self.logger.error("保存客户经理分配关系失败")
                return False
            
        except Exception as e:
            self.logger.error(f"保存分配关系到数据库时出错: {str(e)}")
            return False


def assign_managers_to_customers(managers: List[Dict], customers: List[Dict]) -> Dict[str, List[str]]:
    """
    分配客户给经理的便捷函数
    
    Args:
        managers: 经理数据列表
        customers: 客户数据列表
        
    Returns:
        经理ID到客户ID列表的映射
    """
    assignment = ManagerClientAssignment(managers, customers)
    return assignment.assign_clients()
