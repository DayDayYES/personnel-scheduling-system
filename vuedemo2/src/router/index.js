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
            {
                path: '/Home',
                name: 'home',
                meta: {
                    title: '首页'
                },
                component:()=>import('../components/Home.vue'),
            },
            {
                path: '/ProcessManage',
                name: 'processManage',
                meta: {
                    title: '工序管理'
                },
                component:()=>import('../components/process/ProcessManage.vue'),
            },
            {
                path: '/UserManage',
                name: 'userManage',
                meta: {
                    title: '人员管理'
                },
                component:()=>import('../components/user/UserManage.vue'),
            },
            {
                path: '/Test',
                name: 'test',
                meta: {
                    title: '调度算法'
                },
                component:()=>import('../components/user/ScheduleRun.vue'),
            },
            {
                path: '/ScheduleGantt',
                name: 'scheduleGantt',
                meta: {
                    title: 'DHTMLX Gantt测试'
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