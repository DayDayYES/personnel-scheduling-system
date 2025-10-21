# -*- coding: utf-8 -*-
"""
测试脚本 - 验证工序数据库完整工作流程
"""

from db_connector import DatabaseConnector
from scheduling_environment import create_sample_workpoints_data

def test_save_and_load_workflow():
    """测试保存和加载工序的完整流程"""
    
    print("=" * 80)
    print("测试工序数据库完整工作流程")
    print("=" * 80)
    
    # 第一步：保存示例工序到数据库
    print("\n【第一步】保存示例工序数据到数据库")
    print("-" * 80)
    
    sample_data = create_sample_workpoints_data()
    
    db = DatabaseConnector(
        host="localhost",
        user="root",
        password="123456",
        database="secret"
    )
    
    if not db.connect():
        print("❌ 数据库连接失败，测试终止")
        return False
    
    # 保存所有工作点工序
    save_success = db.save_all_workpoints_processes(sample_data, clear_existing=True)
    db.close()
    
    if not save_success:
        print("❌ 保存工序数据失败")
        return False
    
    # 第二步：从数据库读取工序
    print("\n【第二步】从数据库读取工序数据")
    print("-" * 80)
    
    if not db.connect():
        print("❌ 数据库连接失败，测试终止")
        return False
    
    loaded_data = db.load_all_workpoints_processes()
    db.close()
    
    if loaded_data is None:
        print("❌ 读取工序数据失败")
        return False
    
    # 第三步：验证数据一致性
    print("\n【第三步】验证数据一致性")
    print("-" * 80)
    
    # 检查工作点数量
    if len(loaded_data) != len(sample_data):
        print(f"❌ 工作点数量不匹配: 原始={len(sample_data)}, 读取={len(loaded_data)}")
        return False
    
    print(f"✅ 工作点数量一致: {len(loaded_data)}")
    
    # 检查每个工作点的工序数量
    all_match = True
    for wp_id in sample_data:
        if wp_id not in loaded_data:
            print(f"❌ 工作点 {wp_id} 未找到")
            all_match = False
            continue
        
        original_steps = sample_data[wp_id].get("steps", [])
        loaded_steps = loaded_data[wp_id].get("steps", [])
        
        # 如果原始数据为空（使用标准模板），则跳过详细比较
        if not original_steps:
            print(f"✅ {loaded_data[wp_id]['name']}: {len(loaded_steps)} 个工序（使用标准模板）")
            continue
        
        if len(original_steps) != len(loaded_steps):
            print(f"❌ {loaded_data[wp_id]['name']}: 工序数量不匹配 原始={len(original_steps)}, 读取={len(loaded_steps)}")
            all_match = False
        else:
            print(f"✅ {loaded_data[wp_id]['name']}: {len(loaded_steps)} 个工序")
            
            # 详细检查每个工序
            for i, (orig_step, loaded_step) in enumerate(zip(original_steps, loaded_steps)):
                if orig_step['name'] != loaded_step['name']:
                    print(f"   ⚠️  工序{i+1}名称不匹配: {orig_step['name']} != {loaded_step['name']}")
                    all_match = False
                if orig_step['order'] != loaded_step['order']:
                    print(f"   ⚠️  工序{i+1}顺序不匹配: {orig_step['order']} != {loaded_step['order']}")
                    all_match = False
                if orig_step['team'] != loaded_step['team']:
                    print(f"   ⚠️  工序{i+1}团队不匹配: {orig_step['team']} != {loaded_step['team']}")
                    all_match = False
    
    if not all_match:
        print("\n❌ 数据验证失败：存在不匹配项")
        return False
    
    print("\n✅ 数据验证成功：所有数据一致")
    
    # 第四步：显示读取的数据摘要
    print("\n【第四步】数据摘要")
    print("-" * 80)
    
    for wp_id, wp_data in loaded_data.items():
        wp_name = wp_data.get("name", wp_id)
        steps = wp_data.get("steps", [])
        
        print(f"\n📋 {wp_name} ({wp_id})")
        print(f"   工序总数: {len(steps)}")
        
        # 按阶段统计
        stage_count = {}
        for step in steps:
            order = step['order']
            if order not in stage_count:
                stage_count[order] = []
            stage_count[order].append(step['name'])
        
        print(f"   阶段数量: {len(stage_count)}")
        for order in sorted(stage_count.keys()):
            processes = stage_count[order]
            parallel_flag = " (可并行)" if any(s.get('parallel', False) for s in steps if s['order'] == order) else ""
            print(f"     阶段{order}: {len(processes)}个工序{parallel_flag}")
            for proc_name in processes:
                print(f"       - {proc_name}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成：工序数据库工作流程正常")
    print("=" * 80)
    
    return True


if __name__ == '__main__':
    success = test_save_and_load_workflow()
    
    if success:
        print("\n🎉 所有测试通过！")
        print("\n💡 下一步可以运行 main.py，它会自动从数据库加载工序数据")
    else:
        print("\n❌ 测试失败，请检查错误信息")

