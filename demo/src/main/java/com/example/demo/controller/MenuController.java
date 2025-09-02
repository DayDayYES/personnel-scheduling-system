package com.example.demo.controller;


import com.example.demo.common.Result;
import com.example.demo.entity.Menu;
import com.example.demo.entity.User;
import com.example.demo.service.MenuService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.xml.ws.soap.Addressing;
import java.util.List;

/**
 * <p>
 *  前端控制器
 * </p>
 *
 * @author demo
 * @since 2025-01-10
 */
@RestController
@RequestMapping("/menu")
public class MenuController {

    @Autowired
    private MenuService menuService;
    @GetMapping("/list")
    public Result list(@RequestParam String roleId){
        List list = menuService.lambdaQuery().like(Menu::getMenuright,roleId).list();
        return Result.suc(list);
    }

}
