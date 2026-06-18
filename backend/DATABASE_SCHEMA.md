# TaskFlow 数据库表结构

> 数据库类型: SQLite  
> ORM: SQLAlchemy  
> 最新更新: 2026-06-17

---

## 表总览

| 表名 | 模型 | 用途 |
|------|------|------|
| `users` | User | 用户账户 |
| `tasks` | Task | 日常任务看板的简单任务 |
| `projects` | Project | 工作周报的项目 |
| `work_items` | WorkItem | 工作周报的任务/工单（统一模型，type区分） |
| `work_logs` | WorkLog | 工时记录 |
| `milestones` | Milestone | 任务里程碑 |
| `weekly_targets` | WeeklyTarget | 每周目标工时 |

---

## 1. users — 用户

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | 主键 |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE, INDEX | 邮箱（登录用） |
| `hashed_password` | VARCHAR(255) | NOT NULL | bcrypt 哈希密码 |
| `created_at` | DATETIME | DEFAULT now | 创建时间 |
| `updated_at` | DATETIME | DEFAULT now, ON UPDATE | 更新时间 |

**关系**: `User.tasks` → Task (cascade delete)

---

## 2. tasks — 日常任务

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | 主键 |
| `title` | VARCHAR(255) | NOT NULL | 任务标题 |
| `description` | TEXT | nullable | 任务描述 |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'todo' | todo / in_progress / done |
| `priority` | VARCHAR(10) | NOT NULL, DEFAULT 'medium' | low / medium / high |
| `column_order` | INTEGER | NOT NULL, DEFAULT 0 | 列内排序 |
| `due_date` | DATETIME | nullable | 截止日期 |
| `assignee` | VARCHAR(100) | nullable | 负责人 |
| `tags` | TEXT | nullable | 标签（逗号分隔） |
| `user_id` | INTEGER | FK → users.id, NOT NULL | 所属用户 |
| `created_at` | DATETIME | DEFAULT now | 创建时间 |
| `updated_at` | DATETIME | DEFAULT now, ON UPDATE | 更新时间 |

**索引**:
- `ix_tasks_user_id` on `user_id`
- `ix_tasks_status` on `status`
- `ix_tasks_priority` on `priority`
- `ix_tasks_user_status_order` on `(user_id, status, column_order)`

---

## 3. projects — 项目

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | 主键 |
| `name` | VARCHAR(100) | NOT NULL | 项目名称 |
| `color` | VARCHAR(20) | NOT NULL, DEFAULT '#6366f1' | 项目颜色 |
| `description` | TEXT | nullable | 项目描述 |
| `user_id` | INTEGER | FK → users.id, NOT NULL | 所属用户 |
| `created_at` | DATETIME | DEFAULT now | 创建时间 |

**索引**: `ix_projects_user_id` on `user_id`

**关系**: `Project.work_items` → WorkItem (cascade delete)

---

## 4. work_items — 工作任务/工单

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | 主键 |
| `project_id` | INTEGER | FK → projects.id, NOT NULL | 所属项目 |
| `type` | VARCHAR(20) | NOT NULL, DEFAULT 'task' | task / work_order |
| `title` | VARCHAR(255) | NOT NULL | 标题 |
| `description` | TEXT | nullable | 描述 |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'todo' | todo / in_progress / done |
| `priority` | VARCHAR(10) | NOT NULL, DEFAULT 'medium' | low / medium / high |
| `estimated_hours` | FLOAT | nullable | 预估工时 |
| `week_start` | DATE | NOT NULL | 所属周周一日期 |
| `is_cross_week` | BOOLEAN | NOT NULL, DEFAULT false | 是否跨周 |
| `tags` | TEXT | nullable | 标签（逗号分隔） |
| `column_order` | INTEGER | NOT NULL, DEFAULT 0 | 列内排序 |
| `start_date` | DATETIME | nullable | 开始时间 |
| `end_date` | DATETIME | nullable | 结束时间 |
| `due_date` | DATETIME | nullable | 截止日期 |
| `user_id` | INTEGER | FK → users.id, NOT NULL | 所属用户 |
| `created_at` | DATETIME | DEFAULT now | 创建时间 |
| `updated_at` | DATETIME | DEFAULT now, ON UPDATE | 更新时间 |

**索引**:
- `ix_work_items_user_id` on `user_id`
- `ix_work_items_project_id` on `project_id`
- `ix_work_items_type` on `type`
- `ix_work_items_week_start` on `week_start`
- `ix_work_items_project_week` on `(project_id, week_start)`

**关系**:
- `WorkItem.project` → Project
- `WorkItem.work_logs` → WorkLog (cascade delete)
- `WorkItem.milestones` → Milestone (cascade delete)

---

## 5. work_logs — 工时记录

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | 主键 |
| `work_item_id` | INTEGER | FK → work_items.id, NOT NULL | 所属任务 |
| `week_start` | DATE | NOT NULL | 工时所属周周一 |
| `hours` | FLOAT | NOT NULL | 工时（小时） |
| `log_date` | DATE | nullable | 具体日期 |
| `note` | TEXT | nullable | 备注 |
| `is_system` | BOOLEAN | NOT NULL, DEFAULT false | 是否系统自动生成 |
| `milestone_id` | INTEGER | FK → milestones.id, ON DELETE SET NULL | 关联里程碑 |
| `user_id` | INTEGER | FK → users.id, NOT NULL | 所属用户 |
| `created_at` | DATETIME | DEFAULT now | 创建时间 |

**索引**:
- `ix_work_logs_work_item_id` on `work_item_id`
- `ix_work_logs_week_start` on `week_start`

---

## 6. milestones — 里程碑

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | 主键 |
| `work_item_id` | INTEGER | FK → work_items.id, NOT NULL | 所属任务 |
| `title` | VARCHAR(255) | NOT NULL | 里程碑标题 |
| `description` | TEXT | nullable | 描述 |
| `hours` | FLOAT | nullable | 里程碑工时 |
| `target_date` | DATE | nullable | 目标日期 |
| `is_completed` | BOOLEAN | NOT NULL, DEFAULT false | 是否完成 |
| `completed_at` | DATETIME | nullable | 完成时间 |
| `is_locked` | BOOLEAN | NOT NULL, DEFAULT false | 是否锁定（系统生成） |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | 排序 |
| `user_id` | INTEGER | FK → users.id, NOT NULL | 所属用户 |
| `created_at` | DATETIME | DEFAULT now | 创建时间 |

**索引**: `ix_milestones_work_item_id` on `work_item_id`

---

## 7. weekly_targets — 每周目标工时

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINCREMENT | 主键 |
| `week_start` | DATE | NOT NULL | 所属周周一日期 |
| `target_hours` | FLOAT | NOT NULL, DEFAULT 40.0 | 目标工时（小时） |
| `user_id` | INTEGER | FK → users.id, NOT NULL | 所属用户 |

**索引**: `ix_weekly_targets_week_user` on `(week_start, user_id)` UNIQUE

---

## 表关系图

```
users
  ├── tasks (1:N, cascade)
  ├── projects (1:N)
  ├── work_items (1:N)
  ├── work_logs (1:N)
  ├── milestones (1:N)
  └── weekly_targets (1:N)

projects
  └── work_items (1:N, cascade)

work_items
  ├── work_logs (1:N, cascade)
  └── milestones (1:N, cascade)

work_logs
  └── milestones (N:1, SET NULL on delete)
```

---

## 关键业务规则

1. **拖拽到完成**: WorkItem 状态变为 `done` 时，自动创建一条系统工时记录 (`is_system=true`) 和一个锁定里程碑 (`is_locked=true`)
2. **拖出完成**: 状态从 `done` 移出时，自动删除关联的系统工时和锁定里程碑
3. **时间**: 所有时间均为北京时间 (`datetime.now()`)，非 UTC
4. **标签**: `tasks.tags` 和 `work_items.tags` 均为 TEXT 类型，逗号分隔存储，API 返回时转为数组
