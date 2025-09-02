<template>
    <div class="user-manage-container">
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="header-content">
          <div class="title-section">
            <h2 class="page-title">
              <i class="el-icon-user-solid title-icon"></i>
              人员管理
            </h2>
            <p class="page-subtitle">管理系统用户信息，包括账号、角色等</p>
          </div>
          <div class="header-actions">
            <el-button type="primary" icon="el-icon-plus" @click="add" class="add-btn">
              新增用户
            </el-button>
          </div>
        </div>
      </div>
  
      <!-- 搜索过滤区域 -->
      <div class="filter-section">
        <el-card class="filter-card" shadow="never">
          <div class="filter-content">
            <div class="filter-left">
              <div class="filter-item">
                <label class="filter-label">姓名：</label>
                <el-input 
                  v-model="name" 
                  placeholder="请输入姓名搜索" 
                  suffix-icon="el-icon-search" 
                  class="filter-input"
                  @keyup.enter.native="loadPost"
                  clearable>
                </el-input>
              </div>
              <div class="filter-item">
                <label class="filter-label">性别：</label>
                <el-select v-model="sex" placeholder="请选择性别" class="filter-select" clearable>
                  <el-option
                    v-for="item in sexs"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value">
                  </el-option>
                </el-select>
              </div>
            </div>
            <div class="filter-actions">
              <el-button type="primary" icon="el-icon-search" @click="loadPost">
                查询
              </el-button>
              <el-button icon="el-icon-refresh" @click="resetParam">
                重置
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
  
      <!-- 数据表格区域 -->
      <div class="table-section">
        <el-card class="table-card" shadow="never">
          <div class="table-header">
            <div class="table-title">
              <span class="title-text">用户列表</span>
              <el-tag type="info" class="count-tag">共 {{ total }} 条记录</el-tag>
            </div>
          </div>
          
          <el-table 
            :data="tableData"
            class="user-table"
            stripe
            @selection-change="handleSelectionChange">
            
            <el-table-column type="selection" width="55" align="center"></el-table-column>
            
            <el-table-column prop="id" label="ID" width="80" align="center">
              <template slot-scope="scope">
                <el-tag size="mini" type="info"># {{ scope.row.id }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="no" label="账号" width="140" show-overflow-tooltip>
              <template slot-scope="scope">
                <div class="user-account">
                  <i class="el-icon-user account-icon"></i>
                  {{ scope.row.no }}
                </div>
              </template>
            </el-table-column>
  
            <el-table-column prop="name" label="姓名" width="120" show-overflow-tooltip>
              <template slot-scope="scope">
                <div class="user-name">
                  <el-avatar :size="32" class="user-avatar">
                    {{ scope.row.name ? scope.row.name.charAt(0) : 'U' }}
                  </el-avatar>
                  <span class="name-text">{{ scope.row.name }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="age" label="年龄" width="80" align="center">
              <template slot-scope="scope">
                <el-tag size="small" type="warning">{{ scope.row.age }}岁</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="sex" label="性别" width="80" align="center">
              <template slot-scope="scope">
                <el-tag
                  :type="scope.row.sex == '1' ? 'primary' : 'success'"
                  size="small"
                  class="gender-tag">
                  <i :class="scope.row.sex == '1' ? 'el-icon-male' : 'el-icon-female'"></i>
                  {{ scope.row.sex == '1' ? '男' : '女' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="phone" label="电话" width="140" show-overflow-tooltip>
              <template slot-scope="scope">
                <div class="phone-info">
                  <i class="el-icon-phone phone-icon"></i>
                  {{ scope.row.phone }}
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="roleId" label="角色" width="120" align="center">
              <template slot-scope="scope">
                <el-tag
                  :type="scope.row.roleId == '0' ? 'danger' : (scope.row.roleId == '1' ? 'warning' : 'success')"
                  size="small"
                  class="role-tag">
                  <i class="el-icon-star-on"></i>
                  {{ scope.row.roleId == '0' ? '超级管理员' : (scope.row.roleId == '1' ? '管理员' : '普通用户') }}
                </el-tag>
              </template>
            </el-table-column>
  
            <el-table-column label="操作" width="160" align="center" fixed="right">
              <template slot-scope="scope">
                <div class="action-buttons">
                  <el-button 
                    size="mini" 
                    type="primary" 
                    icon="el-icon-edit"
                    @click="mod(scope.row)"
                    class="action-btn">
                    编辑
                  </el-button>
                  <el-popconfirm
                    title="确定要删除这个用户吗？"
                    @confirm="del(scope.row.id)"
                    icon="el-icon-info"
                    icon-color="red">
                    <el-button 
                      slot="reference"
                      size="mini" 
                      type="danger" 
                      icon="el-icon-delete"
                      class="action-btn">
                      删除
                    </el-button>
                  </el-popconfirm>
                </div>
              </template>
            </el-table-column>
          </el-table>
  
          <!-- 分页组件 -->
          <div class="pagination-container">
            <el-pagination
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :current-page="pageNum"
              :page-sizes="[5, 10, 20, 50]"
              :page-size="pageSize"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
              class="pagination">
            </el-pagination>
          </div>
        </el-card>
      </div>
  
      <!-- 用户表单对话框 -->
      <el-dialog
        :title="isDisabled ? '编辑用户' : '新增用户'"
        :visible.sync="centerDialogVisible"
        width="500px"
        :close-on-click-modal="true"
        :modal="true"
        :lock-scroll="false"
        append-to-body
        class="user-dialog">
        
        <el-form 
          ref="form" 
          :rules="rules" 
          :model="form" 
          label-width="80px"
          class="user-form">
  
          <el-form-item prop="no" label="账号">
            <el-input 
              v-model="form.no" 
              :disabled="isDisabled"
              placeholder="请输入账号"
              prefix-icon="el-icon-user">
            </el-input>
          </el-form-item>
  
          <el-form-item prop="name" label="姓名">
            <el-input 
              v-model="form.name"
              placeholder="请输入姓名"
              prefix-icon="el-icon-s-custom">
            </el-input>
          </el-form-item>
  
          <el-form-item prop="password" label="密码">
            <el-input 
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="el-icon-lock"
              show-password>
            </el-input>
          </el-form-item>
  
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="性别">
                <el-radio-group v-model="form.sex" class="gender-radio">
                  <el-radio label="1">
                    <i class="el-icon-male"></i> 男
                  </el-radio>
                  <el-radio label="0">
                    <i class="el-icon-female"></i> 女
                  </el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item prop="age" label="年龄">
                <el-input 
                  v-model="form.age"
                  placeholder="请输入年龄"
                  prefix-icon="el-icon-time">
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
  
          <el-form-item prop="phone" label="电话">
            <el-input 
              v-model="form.phone"
              placeholder="请输入手机号码"
              prefix-icon="el-icon-phone">
            </el-input>
          </el-form-item>
        </el-form>
  
        <span slot="footer" class="dialog-footer">
          <el-button @click="centerDialogVisible = false" class="cancel-btn">
            取 消
          </el-button>
          <el-button type="primary" @click="save" :loading="saveLoading" class="save-btn">
            {{ saveLoading ? '保存中...' : '确 定' }}
          </el-button>
        </span>
      </el-dialog>
    </div>
  </template>
  
  <script>
  export default {
    name: "UserManage",
    data() {
      let checkAge = (rule, value, callback) => {
        if (value < 18) {
          callback(new Error('年龄必须大于18岁'));
        } else {
          callback();
        }
      };
      let checkDuplicate = (rule, value, callback) => {
        if(this.form.id){
          return callback();
        }
        this.$axios.get(this.$httpUrl + '/user/findByNo?no=' + this.form.no).then(res=>res.data).then(res => {
          if (res.code != 200) {
            callback();
          } else {
            callback(new Error('账号已存在'));
          }
        })
      };
      return {
        tableData: [],
        pageSize: 20,
        pageNum: 1,
        total: 0,
        name: '',
        sex: '',
        sexs: [
          {value: '1', label: '男'},
          {value: '0', label: '女'}
        ],
        centerDialogVisible: false,
        saveLoading: false,
        multipleSelection: [],
        form: {
          id:'',
          no: '',
          password: '',
          name: '',
          age: '',
          sex: '1',
          phone: '',
          roleId: '2',
        },
        rules: {
          no: [
            {required: true, message: '请输入账号', trigger: 'blur'},
            {min: 3, max: 8, message: '长度在 3 到 8 个字符', trigger: 'blur'},
            {validator:checkDuplicate, trigger: 'blur'}
          ],
          name: [
            {required: true, message: '请输入姓名', trigger: 'blur'},
          ],
          password: [
            {required: true, message: '请输入密码', trigger: 'blur'},
            {min: 3, max: 8, message: '长度在 3 到 8 个字符', trigger: 'blur'}
          ],
          age: [
            {required: true, message: '请输入年龄', trigger: 'blur'},
            {min: 1, max: 3, message: '长度在 1 到 3 个字符', trigger: 'blur'},
            {pattern: /^([1-9][0-9]*){1,3}$/, message: '请输入正确的年龄', trigger: 'blur'},
            {validator:checkAge, trigger: 'blur'}
          ],
          phone: [
            {required: true, message: '手机号不能为空', trigger: 'blur'},
            {pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/, message: '请输入正确的手机号', trigger: 'blur'}
          ],
        },
        isDisabled: false,
      };
    },
    methods: {
      handleSelectionChange(val) {
        this.multipleSelection = val;
      },
      resetForm() {
        this.$refs.form.resetFields();
      },
      add() {
        this.isDisabled = false;
        this.centerDialogVisible = true;
        this.$nextTick(() => {
          this.resetForm();
        });
      },
      del(id){
        this.$axios.get(this.$httpUrl + '/user/del?id='+id).then(res => res.data).then(res => {
          if (res.code == 200) {
            this.$message({
              message: '删除成功!',
              type: 'success'
            });
            this.loadPost();
          } else {
            this.$message({
              message: '删除失败!',
              type: 'error'
            });
          }
        });
      },
      mod(row){
        this.isDisabled = true;
        this.centerDialogVisible = true;
        this.$nextTick(() => {
          this.form.id = row.id;
          this.form.no = row.no;
          this.form.name = row.name;
          this.form.password = '';
          this.form.age = row.age + '';
          this.form.sex = row.sex + '';
          this.form.phone = row.phone;
          this.form.roleId = row.roleId;
        });
      },
      doSave(){
        this.saveLoading = true;
        this.$axios.post(this.$httpUrl + '/user/save', this.form).then(res => res.data).then(res => {
          this.saveLoading = false;
          if (res.code == 200) {
            this.$message({
              message: '保存成功!',
              type: 'success'
            });
            this.centerDialogVisible = false;
            this.loadPost();
          } else {
            this.$message({
              message: '保存失败!',
              type: 'error'
            });
          }
        });
      },
      doMod(){
        this.saveLoading = true;
        this.$axios.post(this.$httpUrl + '/user/update', this.form).then(res => res.data).then(res => {
          this.saveLoading = false;
          if (res.code == 200) {
            this.$message({
              message: '修改成功!',
              type: 'success'
            });
            this.centerDialogVisible = false;
            this.loadPost();
          } else {
            this.$message({
              message: '修改失败!',
              type: 'error'
            });
          }
        });
      },
      save() {
        this.$refs.form.validate((valid) => {
          if (valid) {
            if(this.form.id){
              this.doMod();
            }else{
              this.doSave();
            }
          } else {
            this.$message.warning('请检查表单填写是否正确');
            return false;
          }
        });
      },
      resetParam() {
        this.name = '';
        this.sex = '';
        this.loadPost();
      },
      loadPost() {
        this.$axios.post(this.$httpUrl + '/user/listPageC1', {
          pageNum: this.pageNum,
          pageSize: this.pageSize,
          param: {
            name: this.name,
            sex: this.sex,
            roleId:'2'
          }
        }).then(res => res.data).then(res => {
          if (res.code == 200) {
            this.tableData = res.data;
            this.total = res.total;
          } else {
            this.$message.error('获取数据失败');
          }
        });
      },
      handleSizeChange(val) {
        this.pageNum = 1;
        this.pageSize = val;
        this.loadPost();
      },
      handleCurrentChange(val) {
        this.pageNum = val;
        this.loadPost();
      }
    },
    beforeMount() {
      this.loadPost();
    }
  };
  </script>
  
  <style scoped>
  .user-manage-container {
    padding: 0;
    background: transparent;
  }
  
  /* 页面头部 */
  .page-header {
    margin-bottom: 20px;
  }
  
  .header-content {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: white;
  }
  
  .title-section {
    flex: 1;
  }
  
  .page-title {
    margin: 0 0 8px 0;
    font-size: 28px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .title-icon {
    color: #ffd700;
    font-size: 32px;
  }
  
  .page-subtitle {
    margin: 0;
    opacity: 0.9;
    font-size: 14px;
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
  
  .add-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    backdrop-filter: blur(10px);
  }
  
  .add-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.5);
  }
  
  /* 过滤区域 */
  .filter-section {
    margin-bottom: 20px;
  }
  
  .filter-card {
    border: none;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  }
  
  .filter-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .filter-left {
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
  }
  
  .filter-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .filter-label {
    font-weight: 500;
    color: #606266;
    white-space: nowrap;
  }
  
  .filter-input {
    width: 200px;
  }
  
  .filter-select {
    width: 150px;
  }
  
  .filter-actions {
    display: flex;
    gap: 12px;
  }
  
  /* 表格区域 */
  .table-section {
    margin-bottom: 20px;
  }
  
  .table-card {
    border: none;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  }
  
  .table-header {
    padding: 16px 0;
    border-bottom: 1px solid #ebeef5;
    margin-bottom: 16px;
  }
  
  .table-title {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .title-text {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
  
  .count-tag {
    font-size: 12px;
  }
  
  /* 表格样式 */
  .user-table {
    width: 100%;
  }
  
  .user-table :deep(.el-table__header) {
    background: #f8f9fa;
  }
  
  .user-table :deep(.el-table th) {
    background: #f8f9fa !important;
    color: #606266;
    font-weight: 600;
  }
  
  .user-account {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .account-icon {
    color: #909399;
  }
  
  .user-name {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .user-avatar {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    font-weight: 600;
  }
  
  .name-text {
    font-weight: 500;
  }
  
  .gender-tag, .role-tag {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  
  .phone-info {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .phone-icon {
    color: #67c23a;
  }
  
  .action-buttons {
    display: flex;
    gap: 8px;
    justify-content: center;
  }
  
  .action-btn {
    padding: 5px 12px;
    border-radius: 6px;
  }
  
  /* 分页 */
  .pagination-container {
    display: flex;
    justify-content: center;
    padding: 20px 0;
    border-top: 1px solid #ebeef5;
    margin-top: 16px;
  }
  
  /* 对话框样式 */
  .user-dialog :deep(.el-dialog) {
    border-radius: 12px;
    overflow: hidden;
  }
  
  .user-dialog :deep(.el-dialog__header) {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 20px 24px;
  }
  
  .user-dialog :deep(.el-dialog__title) {
    color: white;
    font-weight: 600;
  }
  
  .user-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
    color: white;
  }
  
  .user-form {
    padding: 24px;
  }
  
  .gender-radio {
    display: flex;
    gap: 20px;
  }
  
  .gender-radio :deep(.el-radio__label) {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  
  .dialog-footer {
    padding: 16px 24px;
    border-top: 1px solid #ebeef5;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
  
  .cancel-btn {
    padding: 10px 20px;
  }
  
  .save-btn {
    padding: 10px 20px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
  }
  
  .save-btn:hover {
    background: linear-gradient(135deg, #5a67d8, #6b46c1);
  }

  .user-dialog :deep(.el-dialog__wrapper) {
    z-index: 2000;
  }

  .user-dialog :deep(.el-overlay) {
    z-index: 1999;
  }

  .user-dialog :deep(.el-dialog) {
    position: relative;
    z-index: 2001;
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .header-content {
      flex-direction: column;
      gap: 16px;
      text-align: center;
    }
    
    .filter-content {
      flex-direction: column;
      align-items: stretch;
    }
    
    .filter-left {
      justify-content: center;
    }
    
    .filter-actions {
      justify-content: center;
    }
    
    .user-dialog {
      width: 90% !important;
    }
  }
  </style>