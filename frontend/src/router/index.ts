import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/app',
      component: () => import('@/layout/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: 'kanban', name: 'Kanban', component: () => import('@/views/KanbanView.vue') },
        { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/DashboardView.vue') },
        { path: 'work-weekly', name: 'WorkWeekly', component: () => import('@/views/WorkWeeklyView.vue') },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const stored = localStorage.getItem('auth')
  const isAuth = stored ? JSON.parse(stored).isAuthenticated : false

  if (to.meta.requiresAuth && !isAuth) {
    next('/login')
  } else if (to.meta.guest && isAuth) {
    next('/app/kanban')
  } else {
    next()
  }
})

export default router
