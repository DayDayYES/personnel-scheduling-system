package com.example.demo.mapper;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Constants;
import com.example.demo.entity.User;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.tomcat.util.bcel.classfile.Constant;

/**
 * <p>
 *  Mapper 接口
 * </p>
 *
 * @author demo
 * @since 2024-12-30
 */
@Mapper
public interface UserMapper extends BaseMapper<User> {

    IPage<User> pageC(IPage<User> page);

    IPage<User> pageCC(IPage<User> page, @Param(Constants.WRAPPER) Wrapper wrapper);
}
