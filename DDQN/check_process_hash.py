# -*- coding: utf-8 -*-
"""
工序配置哈希值检查工具
"""

from db_connector import DatabaseConnector
from global_best_tracker import global_best_tracker

def check_workpoints_hash():
    """查看当前工序配置的哈希值并与已保存的对比"""
    print("=" * 60)
    print("工序配置哈希值检查工具")
    print("=" * 60)
    
    print("\n正在从数据库读取工序数据...")
    
    db = DatabaseConnector(
        host="localhost",
        user="root",
        password="123456",
        database="secret"
    )
    
    if not db.connect():
        print("❌ 数据库连接失败")
        return
    
    workpoints_data = db.load_all_workpoints_processes()
    db.close()
    
    if not workpoints_data:
        print("❌ 读取工序数据失败")
        return
    
    # 计算当前配置的哈希值
    current_hash = global_best_tracker.calculate_workpoints_hash(workpoints_data)
    
    # 获取已保存的哈希值
    saved_hash = global_best_tracker.workpoints_hash
    
    print("\n" + "=" * 60)
    print("哈希值对比结果")
    print("=" * 60)
    
    print(f"\n📊 当前工序配置哈希值:")
    print(f"   完整: {current_hash}")
    print(f"   简短: {current_hash[:16]}...")
    
    print(f"\n💾 已保存的配置哈希值:")
    if saved_hash:
        print(f"   完整: {saved_hash}")
        print(f"   简短: {saved_hash[:16]}...")
    else:
        print(f"   无（尚未保存任何最优结果）")
    
    print(f"\n🔍 对比结果:")
    if saved_hash is None:
        print("   ℹ️  尚未保存配置哈希，这是首次运行")
        print("   下次运行将保存当前配置的哈希值")
    elif current_hash == saved_hash:
        print("   ✅ 工序配置未发生变化")
        print("   下次运行将继续使用已有的最优结果（如果存在）")
    else:
        print("   ⚠️  工序配置已发生变化！")
        print("   下次运行将重置全局最优结果，从头开始优化")
    
    # 显示详细的工序信息
    print(f"\n📋 当前工序配置详情:")
    print("=" * 60)
    
    total_steps = 0
    for wp_id, wp_data in sorted(workpoints_data.items()):
        wp_name = wp_data.get("name", wp_id)
        steps = wp_data.get("steps", [])
        total_steps += len(steps)
        
        print(f"\n{wp_name} ({wp_id}):")
        print(f"  工序数量: {len(steps)}")
        
        # 按阶段统计
        stage_stats = {}
        for step in steps:
            order = step.get('order')
            if order not in stage_stats:
                stage_stats[order] = {
                    'count': 0,
                    'parallel_count': 0,
                    'total_duration': 0,
                    'teams': set()
                }
            
            stage_stats[order]['count'] += 1
            if step.get('parallel', False):
                stage_stats[order]['parallel_count'] += 1
            stage_stats[order]['total_duration'] += step.get('duration', 0)
            stage_stats[order]['teams'].add(step.get('team'))
        
        print(f"  阶段数量: {len(stage_stats)}")
        for order in sorted(stage_stats.keys()):
            stats = stage_stats[order]
            parallel_info = f" (其中{stats['parallel_count']}个可并行)" if stats['parallel_count'] > 0 else ""
            print(f"    阶段{order}: {stats['count']}个工序{parallel_info}, "
                  f"总时长≈{stats['total_duration']}, "
                  f"涉及{len(stats['teams'])}个团队")
    
    print(f"\n总计: {len(workpoints_data)}个工作点, {total_steps}个工序")
    
    # 显示已保存的最优结果信息（如果存在）
    best_result = global_best_tracker.get_best_result()
    if best_result['makespan'] != float('inf'):
        print(f"\n🏆 当前保存的全局最优结果:")
        print("=" * 60)
        print(f"  最佳算法: {best_result['algorithm']}")
        print(f"  最佳完工时间: {best_result['makespan']:.2f} 时间单位")
        print(f"  任务数量: {len(best_result['schedule']) if best_result['schedule'] else 0}")
        if best_result['episode'] and best_result['episode'] >= 0:
            print(f"  训练轮次: Episode {best_result['episode']}")
        if best_result['model_path']:
            print(f"  模型路径: {best_result['model_path']}")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)


if __name__ == '__main__':
    try:
        check_workpoints_hash()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

