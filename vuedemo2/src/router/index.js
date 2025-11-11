import VueRouter from "vue-router";

const routes = [
    {
        path: '/',
        name: 'login',
        component:()=>import('../components/Login.vue')
    },
    {
        path: '/Index',
        name: 'index',
        component:()=>import('../components/Index.vue'),
        children: [
            // 系统首页
            {
                path: '/Home',
                name: 'home',
                meta: {
                    title: '系统首页'
                },
                component:()=>import('../components/Home.vue'),
            },
            // 数据采集及处理（工序管理）
            {
                path: '/ProcessManage',
                name: 'processManage',
                meta: {
                    title: '数据采集及处理'
                },
                component:()=>import('../components/process/ProcessManage.vue'),
            },
            // 人员管理（统一路由）
            {
                path: '/UserManage',
                name: 'userManage',
                meta: {
                    title: '人员管理'
                },
                component:()=>import('../components/user/UserManage.vue'),
            },
            // 流程分析资源调配（统一命名，原调度算法）
            {
                path: '/ScheduleAlgorithm',
                name: 'scheduleAlgorithm',
                meta: {
                    title: '流程分析资源调配'
                },
                component:()=>import('../components/user/ScheduleRun.vue'),
            },
            // 保留旧路由 /Test 作为重定向（向后兼容）
            {
                path: '/Test',
                redirect: '/ScheduleAlgorithm'
            },
            // 检验动态驾驶舱（DHTMLX Gantt）
            {
                path: '/ScheduleGantt',
                name: 'scheduleGantt',
                meta: {
                    title: '检验动态驾驶舱'
                },
                component:()=>import('../components/user/ScheduleGantt.vue'),
            },
        ]
    }
]

const router = new VueRouter({
    mode: 'history',
    routes
})

export function resetRouter(){
    router.matcher = new VueRouter({
        mode: 'history',
        routes: []
    }).matcher
}

const VueRouterPush = VueRouter.prototype.push
VueRouter.prototype.push = function push(to){
    return VueRouterPush.call(this, to).catch(err => err)
}

export default router;