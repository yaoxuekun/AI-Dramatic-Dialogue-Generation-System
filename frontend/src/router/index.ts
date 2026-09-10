import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: () => (getStoredToken() ? '/chat' : '/login'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: {
      guestOnly: true,
    },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: {
      guestOnly: true,
    },
  },
  {
    path: '/',
    component: () => import('../components/common/AppLayout.vue'),
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: 'chat',
        name: 'chat',
        component: () => import('../views/ChatView.vue'),
      },
      {
        path: 'chat/:sessionId',
        name: 'chat-session',
        component: () => import('../views/ChatView.vue'),
        props: true,
      },
      {
        path: 'stories',
        name: 'stories',
        component: () => import('../views/StoryList.vue'),
      },
      {
        path: 'outline-options',
        name: 'outline-options',
        component: () => import('../views/OutlineOptionManageView.vue'),
        meta: {
          adminOrRoot: true,
        },
      },
      {
        path: 'prompts',
        name: 'prompts',
        component: () => import('../views/PromptManageView.vue'),
        meta: {
          adminOrRoot: true,
        },
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('../views/UserManageView.vue'),
        meta: {
          rootOnly: true,
        },
      },
      {
        path: 'feature-permissions',
        name: 'feature-permissions',
        component: () => import('../views/FeaturePermissionManageView.vue'),
        meta: {
          rootOnly: true,
        },
      },
      {
        path: 'story/:id',
        name: 'story-detail',
        component: () => import('../views/StoryDetailView.vue'),
        props: true,
      },
      {
        path: 'user',
        name: 'user-center',
        component: () => import('../views/UserCenter.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/chat',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const token = getStoredToken();

  if (to.meta.requiresAuth && !token) {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    };
  }

  if (to.meta.guestOnly && token) {
    return '/chat';
  }

  if (to.meta.rootOnly && getStoredUserRole() !== 'ROOT') {
    return '/chat';
  }

  if (to.meta.adminOrRoot && !isAdminOrRoot(getStoredUserRole())) {
    return '/chat';
  }

  return true;
});

export default router;

function getStoredToken() {
  const token = localStorage.getItem('token');
  if (!token) {
    return '';
  }

  if (isJwtExpired(token)) {
    clearAuthStorage();
    return '';
  }

  return token;
}

function clearAuthStorage() {
  localStorage.removeItem('token');
  localStorage.removeItem('userInfo');
}

function isJwtExpired(token: string) {
  const [, payload] = token.split('.');
  if (!payload) {
    return false;
  }

  try {
    const normalizedPayload = normalizeBase64Url(payload);
    const parsed = JSON.parse(atob(normalizedPayload)) as { exp?: number };
    if (!parsed.exp) {
      return false;
    }
    return parsed.exp * 1000 <= Date.now();
  } catch {
    return false;
  }
}

function normalizeBase64Url(value: string) {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const paddingLength = (4 - (normalized.length % 4)) % 4;
  return normalized + '='.repeat(paddingLength);
}

function getStoredUserRole() {
  const rawUser = localStorage.getItem('userInfo');
  if (!rawUser) {
    return 'USER';
  }

  try {
    const parsed = JSON.parse(rawUser) as { role?: string };
    return parsed.role || 'USER';
  } catch {
    return 'USER';
  }
}

function isAdminOrRoot(role: string) {
  return role === 'ROOT' || role === 'ADMIN';
}
