<template>
  <div style="display:flex;flex-direction:column;height:calc(100vh - 64px);background:transparent">
    <!-- Top Toolbar -->
    <div class="ww-toolbar" style="background:var(--el-bg-color);padding:16px 28px;border-bottom:1px solid var(--el-border-color-light);display:flex;gap:12px;align-items:center;flex-wrap:wrap">
      <!-- Period navigator & view toggle -->
      <div class="period-nav">
        <button class="period-nav-btn" @click="prevPeriod">
          <el-icon size="18"><ArrowLeft /></el-icon>
        </button>
        <span class="period-nav-label">{{ periodLabel }}</span>
        <button class="period-nav-btn" @click="nextPeriod">
          <el-icon size="18"><ArrowRight /></el-icon>
        </button>
        <div class="view-toggle">
          <button :class="['view-toggle-btn', { active: viewMode === 'week' }]" @click="viewMode='week'; onViewModeChange()">
            📆 周
          </button>
          <button :class="['view-toggle-btn', { active: viewMode === 'month' }]" @click="viewMode='month'; onViewModeChange()">
            📅 月
          </button>
        </div>
      </div>

      <!-- Search -->
      <el-input v-model="searchFilter" placeholder="搜索任务..." clearable size="large" style="width:200px"
        :prefix-icon="Search" @input="onSearchChange"/>

      <!-- Project filter -->
      <el-select v-model="projectFilter" placeholder="全部项目" clearable size="large" style="width:150px" @change="onProjectFilterChange">
        <el-option v-for="p in projectStore.projects" :key="p.id" :label="p.name" :value="p.id">
          <span style="display:flex;align-items:center;gap:6px"><span :style="{width:'10px',height:'10px',borderRadius:'50%',background:p.color,display:'inline-block'}"/>{{ p.name }}</span>
        </el-option>
      </el-select>

      <!-- Type filter -->
      <el-select v-model="typeFilter" placeholder="全部类型" clearable size="large" style="width:130px" @change="onTypeFilterChange">
        <el-option label="📋 任务" value="task"/>
        <el-option label="🔧 工单" value="work_order"/>
      </el-select>

      <el-select v-model="tagFilter" placeholder="标签" clearable filterable size="large" style="width:130px" @change="onTagFilterChange">
        <el-option v-for="t in allTags" :key="t" :label="'#' + t" :value="t"/>
      </el-select>

      <!-- Priority filter -->
      <el-select v-model="priorityFilter" placeholder="全部优先级" clearable size="large" style="width:140px" @change="onPriorityFilterChange">
        <el-option v-for="o in priorityFilterOptions" :key="o.value" :value="o.value">
          <span style="display:flex;align-items:center;gap:6px">
            <span :style="{width:'10px',height:'10px',borderRadius:'50%',background:o.dotColor,flexShrink:0}"/>
            {{ o.label }}
          </span>
        </el-option>
      </el-select>

      <!-- Sort -->
      <el-select v-model="sortBy" placeholder="排序" size="large" style="width:140px" @change="onSortChange">
        <el-option label="📅 按日期" value="date"/>
        <el-option label="🔥 按优先级" value="priority"/>
        <el-option label="📅+🔥 日期+优先级" value="date_priority"/>
      </el-select>

      <el-checkbox v-model="overdueFilter" size="large" @change="onOverdueFilterChange" style="height:40px;align-items:center">
        <span style="color:#f56c6c;font-weight:600">⏰ 超期</span>
      </el-checkbox>

      <el-button type="primary" size="large" @click="openCreate" style="margin-left:auto;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:8px">
        <el-icon style="margin-right:4px"><Plus /></el-icon>新建
      </el-button>
      <el-button size="large" @click="showProjectDialog = true" style="border-radius:8px">管理项目</el-button>
      <el-button size="large" @click="handleExport" style="border-radius:8px;font-weight:700">
        <el-icon style="margin-right:4px"><Download /></el-icon>导出
      </el-button>
    </div>

    <!-- Weekday filter bar (week view only) -->
    <div v-if="viewMode === 'week'" class="ww-weekday-bar" style="background:var(--el-bg-color);padding:10px 28px;border-bottom:1px solid var(--el-border-color-light);display:flex;gap:6px;align-items:center">
      <button
        v-for="d in [{value:'',label:'全部'}, ...weekdayOptions]"
        :key="d.value"
        :class="['ww-wd-btn', { 'ww-wd-btn--active': weekdayFilter === d.value }]"
        @click="weekdayFilter = d.value"
      >{{ d.label }}</button>
    </div>

    <!-- Main Content -->
    <div style="flex:1;display:flex;gap:0;overflow:hidden">
      <!-- Left: Work Items List -->
      <div style="flex:1;overflow-y:auto;padding:20px 24px;min-width:0">
        <div v-loading="store.isLoading" style="min-height:200px">
          <!-- Empty state -->
          <div v-if="filteredItems.length === 0 && !store.isLoading" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 20px;color:var(--el-text-color-secondary)">
            <span style="font-size:48px;margin-bottom:12px">📭</span>
            <span style="font-size:15px;font-weight:600">暂无工作任务</span>
            <span style="font-size:13px;margin-top:4px">点击「新建」创建任务或工单</span>
          </div>

          <!-- Grouped by project -->
          <div v-for="group in groupedItems" :key="group.projectId" style="margin-bottom:24px">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
              <span :style="{width:'12px',height:'12px',borderRadius:'3px',background:group.projectColor}"/>
              <span style="font-size:14px;font-weight:700;color:var(--el-text-color-primary)">{{ group.projectName }}</span>
              <span style="font-size:12px;color:var(--el-text-color-secondary)">({{ group.items.length }})</span>
            </div>

            <!-- Status columns for this project -->
            <div style="display:flex;gap:12px">
              <div v-for="col in statusCols" :key="col.key"
                :style="{flex:1,background:col.bg,borderRadius:'12px',padding:'12px',minHeight:'80px',border:'1px solid var(--el-border-color-light)'}"
                @dragover.prevent @drop="onDrop($event, col.key, group)">
                <div style="font-size:12px;font-weight:600;color:var(--el-text-color-secondary);margin-bottom:8px;text-align:center">{{ col.label }}</div>
                <div v-for="(item, idx) in group.items.filter(i => getItemCol(i) === col.key)" :key="item.id"
                  draggable="true"
                  @dragstart="onDragStart($event, item)"
                  @dragover="onDragOver($event, idx)"
                  @dragend="onDragEnd"
                  @click="openEdit(item)"
                  style="background:var(--el-bg-color);border-radius:10px;padding:12px;margin-bottom:8px;cursor:grab;box-shadow:var(--el-box-shadow-light);transition:all 0.2s;border-left:3px solid"
                  :style="{borderLeftColor: isOverdue(item) ? '#f56c6c' : priorityColor(item.priority), background: isOverdue(item) ? 'var(--el-color-danger-light-9)' : 'var(--el-bg-color)'}">
                  <!-- Type badge -->
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap">
                    <span :style="{fontSize:'10px',padding:'0 6px',borderRadius:'4px',fontWeight:600,
                      background:item.type==='work_order'?'var(--el-color-danger-light-9)':'var(--el-color-primary-light-9)',
                      color:item.type==='work_order'?'var(--el-color-danger)':'var(--el-color-primary)'}">
                      {{ item.type === 'work_order' ? '🔧 工单' : '📋 任务' }}
                    </span>
                    <span :style="{fontSize:'11px',padding:'0 6px',borderRadius:'4px',fontWeight:600,background:priorityBg(item.priority),color:priorityColor(item.priority),border:`1px solid ${priorityColor(item.priority)}`}">{{ priorityMap[item.priority] }}</span>
                    <span v-if="isOverdue(item)" style="font-size:10px;padding:0 6px;borderRadius:'4px';fontWeight:600;background:var(--el-color-danger-light-9);color:var(--el-color-danger);border:1px solid var(--el-color-danger)">⏰ 已超期</span>
                  </div>
                  <div style="font-size:13px;font-weight:600;color:var(--el-text-color-primary);margin-bottom:4px;line-height:1.4">
                    <span v-if="item.is_cross_week" style="display:inline-block;font-size:10px;padding:0 5px;margin-right:4px;border-radius:4px;background:var(--el-color-success-light-9);color:var(--el-color-success);border:1px solid var(--el-color-success-light-5);vertical-align:middle;white-space:nowrap">🔁 {{ item.num_weeks }}周</span>
                    <span v-if="item.is_cross_week && item.week_hours" style="display:inline-flex;gap:2px;flex-wrap:wrap;vertical-align:middle">
                      <span v-for="(h, wk) in item.week_hours" :key="wk" style="font-size:9px;padding:0 3px;border-radius:3px;vertical-align:middle;white-space:nowrap" :style="{background:(item.completed_weeks||[]).includes(wk)?'var(--el-color-success-light-9)':'var(--el-fill-color-light)',color:(item.completed_weeks||[]).includes(wk)?'var(--el-color-success)':'var(--el-text-color-placeholder)'}">{{ wk.slice(5) }} {{ (item.completed_weeks||[]).includes(wk) ? '✅' : '⏳' }}</span>
                    </span>
                    {{ item.title }}
                  </div>
                  <!-- Tags row -->
                  <div v-if="(item.tags||[]).length" style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px">
                    <span v-for="t in (item.tags||[])" :key="t" style="background:var(--el-color-primary-light-9);color:var(--el-color-primary);font-size:11px;padding:1px 8px;border-radius:6px;font-weight:500">#{{ t }}</span>
                  </div>
                  <!-- Hours bar -->
                  <div v-if="displayItemHours(item) > 0" style="margin-top:4px">
                    <div style="display:flex;align-items:center;gap:6px">
                      <div style="flex:1;height:6px;background:var(--el-fill-color-light);border-radius:3px;overflow:hidden">
                        <div :style="{width:Math.min(100,getItemHours(item.id)/Math.max(0.01,(item.estimated_hours||1))*100)+'%',height:'100%',borderRadius:'3px',background:getItemHours(item.id)/(item.estimated_hours||1)>=1?'#67c23a':'#6366f1',transition:'width 0.3s'}"/>
                      </div>
                      <span style="font-size:11px;color:var(--el-text-color-secondary);white-space:nowrap">{{ getItemHours(item.id) }}h / {{ item.estimated_hours }}h</span>
                    </div>
                  </div>
                  <!-- Date display with weekday color -->
                  <div style="margin-top:6px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
                    <span v-if="item.start_date" style="font-size:11px;display:flex;align-items:center;gap:2px" :style="{color: getWeekdayColor(item.start_date)}">
                      📅 {{ formatDateDisplay(item.start_date) }} {{ getWeekdayLabel(item.start_date) }}
                    </span>
                    <span v-if="item.end_date" style="font-size:11px" :style="{color: isOverdue(item) ? '#f56c6c' : 'var(--el-text-color-secondary)'}">
                      ⏱️ {{ item.end_date.slice(0, 16).replace('T', ' ') }}
                    </span>
                  </div>
                </div>
                <div v-if="group.items.filter(i => getItemCol(i) === col.key).length===0" style="display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--el-text-color-placeholder);font-size:13px;padding:20px 16px;gap:6px">
                  <span style="font-size:28px;opacity:0.5">{{ col.emptyIcon }}</span>
                  <span>暂无任务</span>
                  <span style="font-size:11px;opacity:0.7">拖拽或新建添加</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Dashboard Panel -->
      <div style="width:390px;flex-shrink:0;background:var(--el-bg-color);border-left:1px solid var(--el-border-color-light);overflow-y:auto;padding:20px">
        <h3 style="font-size:16px;font-weight:700;color:var(--el-text-color-primary);margin-bottom:18px">
          {{ viewMode === 'week' ? '本周' : '本月' }}工时概况
        </h3>

        <!-- Saturation ring -->
        <el-card shadow="never" style="border-radius:12px;margin-bottom:14px;text-align:center">
          <v-chart :option="saturationOption" style="height:220px" autoresize />
          <div style="font-size:13px;color:var(--el-text-color-secondary);margin-top:-12px">
            已记录 <b style="color:var(--el-text-color-primary)">{{ currentStats?.total_hours || 0 }}h</b> / {{ currentStats?.weekly_target || currentStats?.monthly_target || 0 }}h
            <template v-if="(currentStats?.total_hours || 0) > (currentStats?.weekly_target || currentStats?.monthly_target || 0)">
              · <span style="color:#f56c6c;font-weight:600">⚡ 超出 {{ Math.round(((currentStats?.total_hours || 0) - (currentStats?.weekly_target || currentStats?.monthly_target || 0)) * 10) / 10 }}h</span>
            </template>
            <template v-else>
              · 剩余 <b style="color:#67c23a">{{ currentStats?.remaining_hours || 0 }}h</b>
            </template>
          </div>
          <div v-if="currentStats?.is_custom_target && (currentStats?.weekly_target || currentStats?.monthly_target || 40) !== 40" style="font-size:10px;color:#e6a23c;margin-top:2px">📝 自定义目标</div>
          <div v-if="currentNotes" style="font-size:11px;color:var(--el-text-color-secondary);margin-top:4px;max-width:260px;margin-left:auto;margin-right:auto;line-height:1.4">💬 {{ currentNotes }}</div>
          <el-button text size="small" type="primary" style="margin-top:4px" @click="openTargetDialog">⚙️ 设置目标</el-button>
        </el-card>

        <!-- Target Dialog -->
        <el-dialog v-model="targetDialogVisible" width="420px" destroy-on-close>
          <template #header>
            <div style="display:flex;align-items:center;gap:10px">
              <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center">
                <el-icon color="#fff" size="20"><Aim /></el-icon>
              </div>
              <span style="font-size:17px;font-weight:700;color:var(--el-text-color-primary)">设置饱和度目标</span>
            </div>
          </template>
          <div style="text-align:center">
            <div style="font-size:14px;color:var(--el-text-color-secondary);margin-bottom:12px">
              {{ viewMode === 'week' ? '本周' : '本月' }}目标工时
            </div>
            <el-input-number v-model="targetFormHours" :min="1" :max="168" :step="1" size="large" style="width:180px" controls-position="right"/>
            <span style="margin-left:8px;font-size:16px;font-weight:600">h</span>
            <div style="margin-top:14px;display:flex;gap:8px;justify-content:center">
              <el-button size="small" @click="targetFormHours = 8" :type="targetFormHours === 8 ? 'primary' : ''">8h</el-button>
              <el-button size="small" @click="targetFormHours = 16" :type="targetFormHours === 16 ? 'primary' : ''">16h</el-button>
              <el-button size="small" @click="targetFormHours = 24" :type="targetFormHours === 24 ? 'primary' : ''">24h</el-button>
              <el-button size="small" @click="targetFormHours = 32" :type="targetFormHours === 32 ? 'primary' : ''">32h</el-button>
            </div>
          </div>
          <div style="margin-top:14px;text-align:left">
            <div style="font-size:13px;color:var(--el-text-color-secondary);margin-bottom:6px">备注原因（选填）</div>
            <el-input v-model="targetFormNotes" type="textarea" :rows="2" placeholder="如：请假三天、出差" maxlength="200" show-word-limit />
          </div>
          <template #footer>
            <el-button @click="targetDialogVisible = false">取消</el-button>
            <el-button v-if="currentStats?.is_custom_target && (currentStats?.weekly_target || currentStats?.monthly_target || 40) !== 40" type="danger" plain @click="resetTarget">恢复默认</el-button>
            <el-button type="primary" @click="saveTarget" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">保存</el-button>
          </template>
        </el-dialog>

        <!-- Completed hours row -->
        <el-row :gutter="8" style="margin-bottom:8px">
          <el-col :span="12">
            <el-card shadow="hover" :body-style="{ padding:'12px', textAlign:'center' }"
              style="background:var(--el-color-primary-light-9);border:none;border-radius:10px">
              <div style="font-size:20px;font-weight:800;color:var(--el-color-primary)">{{ currentStats?.task_hours || 0 }}h</div>
              <div style="font-size:11px;color:var(--el-color-primary);margin-top:1px;font-weight:600">✅ 已完成任务</div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover" :body-style="{ padding:'12px', textAlign:'center' }"
              style="background:#fdf6ec;border:none;border-radius:10px">
              <div style="font-size:20px;font-weight:800;color:#e6a23c">{{ currentStats?.work_order_hours || 0 }}h</div>
              <div style="font-size:11px;color:#e6a23c;margin-top:1px;font-weight:600">✅ 已完成工单</div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Pending hours row -->
        <el-row :gutter="8" style="margin-bottom:8px">
          <el-col :span="12">
            <el-card shadow="hover" :body-style="{ padding:'12px', textAlign:'center' }"
              style="background:#e8f4fd;border:none;border-radius:10px">
              <div style="font-size:20px;font-weight:800;color:#409eff">{{ currentStats?.pending_task_hours || 0 }}h</div>
              <div style="font-size:11px;color:#409eff;margin-top:1px;font-weight:600">⏳ 待处理任务</div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover" :body-style="{ padding:'12px', textAlign:'center' }"
              style="background:#fef0f0;border:none;border-radius:10px">
              <div style="font-size:20px;font-weight:800;color:#f56c6c">{{ currentStats?.pending_work_order_hours || 0 }}h</div>
              <div style="font-size:11px;color:#f56c6c;margin-top:1px;font-weight:600">📦 待处理工单</div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Remaining / Over -->
        <el-card shadow="hover" :body-style="{ padding:'12px', textAlign:'center' }"
          :style="{ background: (currentStats?.available_hours ?? 0) >= 0 ? '#f0f9eb' : '#fef0f0', border:'none', borderRadius:'10px', marginBottom:'14px' }">
          <div :style="{ fontSize:'20px', fontWeight:800, color: (currentStats?.available_hours ?? 0) >= 0 ? '#67c23a' : '#f56c6c' }">{{ Math.abs(currentStats?.available_hours || 0) }}h</div>
          <div :style="{ fontSize:'11px', color: (currentStats?.available_hours ?? 0) >= 0 ? '#67c23a' : '#f56c6c', marginTop:'1px', fontWeight:600 }">{{ (currentStats?.available_hours ?? 0) >= 0 ? '🎯 剩余可投入' : '⚡ 预计超出' }}</div>
        </el-card>

        <!-- Project breakdown bar chart -->
        <el-card v-if="(currentStats?.project_breakdown||[]).length" shadow="never" style="border-radius:12px;margin-bottom:14px">
          <template #header><span style="font-weight:700;font-size:13px">按项目分布</span></template>
          <v-chart :option="projectBarOption" style="height:180px" autoresize />
        </el-card>

        <!-- Daily hours by weekday -->
        <el-card shadow="never" style="border-radius:12px;margin-bottom:14px">
          <template #header>
            <div style="display:flex;align-items:center;justify-content:space-between">
              <span style="font-weight:700;font-size:13px">每日工时分布（周一~周日）</span>
              <span style="font-size:12px;color:var(--el-text-color-secondary)">总计 <b style="color:var(--el-color-primary)">{{ dailyHours.reduce((a,b) => a + b, 0) }}h</b></span>
            </div>
          </template>
          <v-chart :option="dailyBarOption" style="height:200px" autoresize />
        </el-card>

        <!-- Trend line chart -->
        <el-card shadow="never" style="border-radius:12px;margin-bottom:14px">
          <template #header>
            <div style="display:flex;align-items:center;justify-content:space-between">
              <span style="font-weight:700;font-size:13px">工时趋势</span>
              <span style="font-size:11px;color:var(--el-text-color-secondary)">近12周 · 最高 {{ Math.max(...trendData.map(d=>d.total_hours), 0) }}h</span>
            </div>
          </template>
          <v-chart v-if="trendData.length" :option="trendOption" style="height:220px" autoresize />
          <div v-else style="text-align:center;color:var(--el-text-color-secondary);font-size:12px;padding:20px">加载中...</div>
        </el-card>
      </div>
    </div>

    <!-- WorkItem Dialog -->
    <el-dialog v-model="dialogVisible" width="1000px" destroy-on-close class="ww-dialog">
      <template #header>
        <div style="display:flex;align-items:center;gap:10px">
          <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center">
            <el-icon color="#fff" size="18"><EditPen v-if="editingItem"/><Plus v-else/></el-icon>
          </div>
          <span style="font-size:17px;font-weight:700;color:var(--el-text-color-primary)">{{ editingItem ? '编辑工作项' : '创建工作项' }}</span>
        </div>
      </template>
      <el-form :model="itemForm" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item :error="formErrors.title">
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><EditPen/></el-icon> 标题</span></template>
              <el-input v-model="itemForm.title" placeholder="标题" size="large"/>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Folder/></el-icon> 项目</span></template>
              <el-select v-model="itemForm.project_id" style="width:100%" size="large">
                <el-option v-for="p in projectStore.projects" :key="p.id" :label="p.name" :value="p.id"/>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><List/></el-icon> 类型</span></template>
              <el-select v-model="itemForm.type" style="width:100%" size="large">
                <el-option label="📋 任务" value="task"/>
                <el-option label="🔧 工单" value="work_order"/>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Flag/></el-icon> 优先级</span></template>
              <el-select v-model="itemForm.priority" style="width:100%" size="large">
                <el-option v-for="o in priorityOptions" :key="o.value" :label="o.label" :value="o.value"/>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Document/></el-icon> 描述</span></template>
          <TiptapEditor ref="editorRef" v-model="itemForm.description" />
        </el-form-item>
        <!-- Attachments -->
        <el-form-item>
          <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Paperclip/></el-icon> 附件</span></template>
          <div style="width:100%">
            <!-- File list -->
            <div v-if="itemForm.attachments.length" style="border:1px solid var(--el-border-color-lighter);border-radius:6px;overflow:hidden;margin-bottom:8px">
              <div v-for="(att, idx) in itemForm.attachments" :key="att.url" style="display:flex;align-items:center;padding:6px 10px;gap:8px;border-bottom:1px solid var(--el-border-color-lighter);font-size:13px" :style="{background: idx%2===0?'var(--el-fill-color-lighter)':'var(--el-fill-color-blank)'}">
                <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--el-text-color-primary);cursor:pointer" @click="openAttach(att.url)" :title="att.name">{{ att.name }}</span>
                <span style="color:var(--el-text-color-placeholder);font-size:11px;white-space:nowrap">{{ formatFileSize(att.size) }}</span>
                <el-button type="danger" link size="small" @click="removeAttach(idx)"><el-icon><Delete/></el-icon></el-button>
              </div>
            </div>
            <!-- Drop zone -->
            <div
              class="attach-drop-zone"
              :class="{ 'attach-dragover': attachDragover }"
              @click="attachInput?.click()"
              @dragover.prevent="attachDragover = true"
              @dragleave="attachDragover = false"
              @drop.prevent="handleAttachDrop"
            >
              <el-icon :size="22"><Upload/></el-icon>
              <span>拖拽文件到此处，或点击上传</span>
              <input ref="attachInput" type="file" style="display:none" @change="handleAttachPick" multiple />
            </div>
          </div>
        </el-form-item>
        <!-- Cross-week -->
        <el-form-item>
          <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><RefreshRight/></el-icon> 跨周设置</span></template>
          <div style="width:100%">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
              <el-switch v-model="crossWeekEnabled" active-text="跨周任务" inactive-text="" size="large" />
              <span v-if="crossWeekEnabled" style="font-size:12px;color:var(--el-text-color-secondary)">
                跨度 {{ weekList.length }} 周，预估工时由各周之和自动计算
              </span>
            </div>
            <template v-if="crossWeekEnabled">
              <el-row :gutter="12" style="margin-bottom:12px">
                <el-col :span="12">
                  <span style="font-size:12px;color:var(--el-text-color-secondary);margin-bottom:4px;display:block">起始周（周一）</span>
                  <el-date-picker v-model="crossWeekStart" type="date" placeholder="起始周一" style="width:100%" size="large" format="YYYY-MM-DD" value-format="YYYY-MM-DD" :disabled-date="disableNonMonday" @change="rebuildWeekHours" />
                </el-col>
                <el-col :span="12">
                  <span style="font-size:12px;color:var(--el-text-color-secondary);margin-bottom:4px;display:block">截止周（周一）</span>
                  <el-date-picker v-model="crossWeekEnd" type="date" placeholder="截止周一" style="width:100%" size="large" format="YYYY-MM-DD" value-format="YYYY-MM-DD" :disabled-date="disableNonMonday" @change="rebuildWeekHours" />
                </el-col>
              </el-row>
              <!-- Weekly hour allocation -->
              <div v-if="weekList.length > 0" style="border:1px solid var(--el-border-color-lighter);border-radius:8px;overflow:hidden">
                <div v-for="(w, idx) in weekList" :key="w.key" style="display:flex;align-items:center;padding:6px 12px;gap:10px;border-bottom:1px solid var(--el-border-color-lighter);font-size:13px" :style="{background:idx%2===0?'var(--el-fill-color-lighter)':'var(--el-fill-color-blank)'}">
                  <span style="width:100px;flex-shrink:0;color:var(--el-text-color-regular);font-weight:500;font-size:12px">{{ getWeekLabel(w.key) }}</span>
                  <el-input-number v-model="w.hours" :min="0" :step="0.5" :precision="1" size="large" style="flex:1" controls-position="right" @change="syncWeekHours" />
                  <span style="color:var(--el-text-color-placeholder);font-size:13px;width:20px;text-align:center;flex-shrink:0">h</span>
                </div>
                <div style="display:flex;align-items:center;padding:6px 12px;gap:10px;font-size:13px;font-weight:600;background:var(--el-fill-color-light)">
                  <span style="width:110px;flex-shrink:0;color:var(--el-text-color-primary)">预估总工时</span>
                  <span style="flex:1;color:var(--el-color-primary)">{{ weekList.reduce((s,w)=>s+(w.hours||0),0).toFixed(1) }} h</span>
                </div>
              </div>
            </template>
          </div>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Calendar/></el-icon> 开始时间</span></template>
              <el-date-picker v-model="itemForm.start_date" type="datetime" placeholder="开始时间" style="width:100%" size="large" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss"/>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Calendar/></el-icon> 结束时间</span></template>
              <el-date-picker v-model="itemForm.end_date" type="datetime" placeholder="结束时间" style="width:100%" size="large" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" :default-time="new Date(2000,0,1,17,30,0)"/>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12" v-if="editingItem">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><List/></el-icon> 状态</span></template>
              <el-select v-model="itemForm.status" style="width:100%" size="large">
                <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value"/>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="editingItem ? 12 : 12">
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Clock/></el-icon> 预估工时(h)</span></template>
              <el-input-number v-model="itemForm.estimated_hours" :min="0" :step="0.5" :precision="1" style="width:100%" size="large" :disabled="crossWeekEnabled"/>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- Tags input -->
        <el-form-item>
          <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><PriceTag/></el-icon> 标签</span></template>
          <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center">
            <el-tag v-for="(t, i) in itemForm.tags" :key="i" closable @close="itemForm.tags.splice(i,1)">{{ t }}</el-tag>
            <el-input v-if="tagInputVisible" ref="tagInputRef" v-model="tagInputValue" size="large" style="width:100px" @keyup.enter="addItemTag" @blur="addItemTag" placeholder="输入标签"/>
            <el-button v-else size="large" @click="showItemTagInput">+ 标签</el-button>
          </div>
        </el-form-item>

        <!-- Milestones section (only when editing) -->
        <div v-if="editingItem" style="margin-bottom:16px">
          <!-- Progress bar in gray block -->
          <div style="background:var(--el-fill-color-light);border-radius:8px;padding:14px 16px;margin-bottom:12px">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:14px;font-weight:700;color:var(--el-text-color-primary)">🚩 里程碑进度</span>
              <span v-if="milestones.length" style="font-size:12px;color:var(--el-text-color-secondary);font-weight:600">{{ milestones.filter(m=>m.is_completed).length }}/{{ milestones.length }}</span>
            </div>
            <el-progress v-if="milestones.length" :percentage="milestoneProgress" :color="progressColor" :stroke-width="12" striped striped-flow/>
            <div v-else style="font-size:12px;color:var(--el-text-color-secondary);text-align:center;padding:4px">暂无里程碑</div>
          </div>

          <!-- Empty state -->
          <div v-if="!milestones.length" style="text-align:center;padding:24px 0;color:var(--el-text-color-secondary)">
            <el-icon size="32" color="#c0c4cc"><Flag/></el-icon>
            <div style="font-size:13px;margin-top:8px">暂无里程碑</div>
            <div style="font-size:12px;margin-top:2px">点击下方按钮添加</div>
          </div>

          <!-- Milestone list -->
          <div v-if="milestones.length" style="max-height:360px;overflow-y:auto;display:flex;flex-direction:column;gap:8px;margin-bottom:12px">
            <div v-for="(m, idx) in milestones" :key="m.id"
              draggable="true"
              @dragstart="onMsDragStart($event, m, idx)"
              @dragover.prevent="onMsDragOver($event, m)"
              @drop="onMsDrop($event, m, idx)"
              @dragend="onMsDragEnd"
              :style="{background: m.is_completed ? 'var(--el-color-success-light-9)' : 'var(--el-bg-color)',borderRadius:'6px',padding:'12px 12px 12px 8px',border:`1px solid ${m.is_completed ? 'var(--el-color-success-light-5)' : 'var(--el-border-color-light)'}`,transition:'all 0.2s',display:'flex',gap:'6px',alignItems:'flex-start',opacity: msDragId === m.id ? 0.5 : 1}">
              <!-- Drag handle -->
              <div style="cursor:grab;color:var(--el-text-color-placeholder);padding-top:2px;user-select:none" title="拖拽排序">☰</div>
              <!-- Checkbox -->
              <el-checkbox :model-value="m.is_completed" @change="toggleMilestone(m)" :disabled="m.is_locked" style="padding-top:2px"/>
              <!-- Content -->
              <div style="flex:1;min-width:0">
                <div :style="{fontSize:'13px',fontWeight:600,color:'var(--el-text-color-primary)',textDecoration: m.is_completed ? 'line-through' : 'none', opacity: m.is_completed ? 0.6 : 1}">{{ m.title }}</div>
                <div v-if="m.description" style="font-size:12px;color:var(--el-text-color-secondary);margin-top:3px;line-height:1.5;word-break:break-word">{{ m.description }}</div>
                <div style="display:flex;align-items:center;gap:12px;margin-top:6px;flex-wrap:wrap">
                  <span v-if="m.week_start" style="font-size:11px;color:var(--el-color-primary);font-weight:500">📅 {{ getWeekLabel(m.week_start) }}</span>
                  <span v-if="m.target_date" style="font-size:11px;color:var(--el-text-color-secondary)">🎯 目标 {{ m.target_date }}</span>
                  <span v-if="m.hours" style="font-size:11px;color:var(--el-text-color-secondary)">⏱ {{ m.hours }}h</span>
                </div>
                <div v-if="m.is_completed && m.completed_at" style="font-size:11px;color:#67c23a;margin-top:3px;font-weight:500">✅ 完成于 {{ m.completed_at.slice(0, 16).replace('T', ' ') }}</div>
              </div>
              <!-- Actions (horizontal) -->
              <div style="display:flex;align-items:center;gap:0;flex-shrink:0">
                <template v-if="m.is_locked">
                  <span style="font-size:11px;color:var(--el-text-color-placeholder);padding:4px" title="系统生成，不可编辑">🔒</span>
                </template>
                <template v-else>
                  <el-button size="small" text @click="openMilestoneDialog(m)"><el-icon><EditPen/></el-icon></el-button>
                  <el-button size="small" text type="danger" @click="removeMilestone(m.id)"><el-icon><Delete/></el-icon></el-button>
                </template>
              </div>
            </div>
          </div>

          <!-- Action buttons below divider -->
          <div style="border-top:1px solid var(--el-border-color-lighter);padding-top:12px;display:flex;gap:10px">
            <el-button @click="openMilestoneDialog()" class="ms-add-btn" :style="hasCompletedMs ? 'flex:1' : 'flex:1'">
              + 添加里程碑
            </el-button>
            <el-button v-if="showClearBtn" @click="clearCompletedMilestones" class="ms-clear-btn" style="flex:1">
              <el-icon style="margin-right:4px"><Delete/></el-icon>清除已完成
            </el-button>
          </div>
        </div>

        <!-- Milestone Dialog -->
        <el-dialog v-model="msDialogVisible" width="460px" destroy-on-close class="ww-dialog">
          <template #header>
            <div style="display:flex;align-items:center;gap:10px">
              <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center">
                <el-icon color="#fff" size="18"><Flag/></el-icon>
              </div>
              <span style="font-size:17px;font-weight:700;color:var(--el-text-color-primary)">{{ editingMilestone ? '编辑里程碑' : '添加里程碑' }}</span>
            </div>
          </template>
          <el-form :model="msForm" label-position="top">
            <el-form-item :error="msErrors.title">
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><EditPen/></el-icon> 标题</span></template>
              <el-input v-model="msForm.title" placeholder="里程碑标题" maxlength="255" size="large"/>
            </el-form-item>
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Clock/></el-icon> 工时 (h)</span></template>
              <el-input-number v-model="msForm.hours" :min="0" :step="0.5" :precision="1" style="width:100%" size="large"/>
            </el-form-item>
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Document/></el-icon> 描述（最多500字）</span></template>
              <el-input v-model="msForm.description" type="textarea" :rows="3" placeholder="里程碑描述" maxlength="500" show-word-limit size="large"/>
            </el-form-item>
            <el-form-item>
              <template #label><span style="display:flex;align-items:center;gap:4px"><el-icon><Calendar/></el-icon> 目标时间</span></template>
              <el-date-picker v-model="msForm.target_date" type="date" placeholder="目标日期" style="width:100%" size="large" format="YYYY-MM-DD" value-format="YYYY-MM-DD"/>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="msDialogVisible=false" size="large">取消</el-button>
            <el-button type="primary" @click="saveMilestone" :loading="savingMs" size="large" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">保存</el-button>
          </template>
        </el-dialog>
      </el-form>
      <template #footer>
        <div style="display:flex;justify-content:space-between">
          <el-button v-if="editingItem" type="danger" @click="handleDelete" plain size="large">删除</el-button>
          <div style="display:flex;gap:8px;margin-left:auto">
            <el-button @click="dialogVisible=false" size="large">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving" size="large" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">保存</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- Project Management Dialog -->
    <el-dialog v-model="showProjectDialog" title="项目管理" width="480px" destroy-on-close>
      <div style="display:flex;gap:8px;margin-bottom:16px">
        <el-input v-model="newProjectName" placeholder="项目名称" size="large" style="flex:1" @keyup.enter="submitProject"/>
        <el-color-picker v-model="newProjectColor" size="large"/>
        <el-button type="primary" size="large" @click="submitProject" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">{{ editingProjectId ? '保存' : '添加' }}</el-button>
        <el-button v-if="editingProjectId" size="large" @click="cancelEditProject">取消</el-button>
      </div>
      <div v-for="p in projectStore.projects" :key="p.id" style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border-radius:8px;margin-bottom:6px;background:var(--el-fill-color-light)">
        <div style="display:flex;align-items:center;gap:8px">
          <span :style="{width:'14px',height:'14px',borderRadius:'4px',background:p.color,display:'inline-block'}"/>
          <span style="font-size:14px;font-weight:600;color:var(--el-text-color-primary)">{{ p.name }}</span>
        </div>
        <div style="display:flex;gap:4px">
          <el-button size="small" text @click="editProject(p)"><el-icon><EditPen/></el-icon></el-button>
          <el-button size="small" text type="danger" @click="removeProject(p.id)"><el-icon><Delete/></el-icon></el-button>
        </div>
      </div>
      <div v-if="projectStore.projects.length===0" style="text-align:center;color:var(--el-text-color-secondary);padding:20px">暂无项目，请先添加</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick, toRaw } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Close, EditPen, Plus, Document, PriceTag, Flag, List, User, Calendar,
  ArrowLeft, ArrowRight, Folder, Clock, Delete, Sunny, Moon, SwitchButton,
  Paperclip, Upload, RefreshRight,
} from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { BarChart, PieChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { useProjectStore } from '@/stores/project'
import { useWorkItemStore } from '@/stores/work-item'
import { useScopeStore } from '@/stores/scope'
import type { WorkItem } from '@/api/work-items'
import { fetchWorkItems, cleanupWorkImages, uploadAttachment as uploadAttachApi } from '@/api/work-items'

interface AttachItem { name: string; url: string; size: number }
import { getWeeklyStats, getTrendStats, getMonthlyStats, type WeeklyStats, type TrendPoint, type MonthlyStats } from '@/api/work-stats'
import { getWeeklyTarget, setWeeklyTarget } from '@/api/weekly-targets'
import { fetchMilestones, createMilestone, updateMilestone, deleteMilestone, reorderMilestones, type Milestone } from '@/api/milestones'
import { PRIORITY_OPTIONS, STATUS_OPTIONS, PRIORITY_MAP } from '@/types'
import { exportWorkWeekly } from '@/utils/export'
import { useChartTheme } from '@/composables/useChartTheme'
import TiptapEditor from '@/components/TiptapEditor.vue'

use([BarChart, PieChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const projectStore = useProjectStore()
const chart = useChartTheme()
const store = useWorkItemStore()
const scope = useScopeStore()

const priorityOptions = PRIORITY_OPTIONS
const statusOptions = STATUS_OPTIONS
const priorityFilterOptions = [
  { value: 'high', label: '高', dotColor: '#f56c6c' },
  { value: 'medium', label: '中', dotColor: '#e6a23c' },
  { value: 'low', label: '低', dotColor: '#67c23a' },
]
const priorityMap = PRIORITY_MAP
const priorityColor = (p: string) => p === 'high' ? '#f56c6c' : p === 'medium' ? '#e6a23c' : '#67c23a'
const priorityBg = (p: string) => p === 'high' ? '#fef0f0' : p === 'medium' ? '#fdf6ec' : '#eefbe6'

const statusCols = [
  { key: 'todo', label: '待处理', bg: 'var(--el-color-primary-light-9)', emptyIcon: '📥' },
  { key: 'in_progress', label: '进行中', bg: 'var(--el-color-warning-light-9)', emptyIcon: '⚡' },
  { key: 'done', label: '已完成', bg: 'var(--el-color-success-light-9)', emptyIcon: '🎉' },
]

// ── Week/Month state ──
const viewMode = ref<'week' | 'month'>('week')
const currentWeekStart = ref(getMonday(new Date()))
const currentMonth = ref({ year: new Date().getFullYear(), month: new Date().getMonth() + 1 })

function getMonday(d: Date): Date {
  const date = new Date(d)
  const day = date.getDay()
  const diff = date.getDate() - day + (day === 0 ? -6 : 1)
  date.setDate(diff)
  date.setHours(0, 0, 0, 0)
  return date
}

function formatDate(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`
}

function formatDateTime(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function getWeekEnd(monday: Date): Date {
  const end = new Date(monday)
  end.setDate(end.getDate() + 6)
  return end
}

const periodLabel = computed(() => {
  if (viewMode.value === 'week') {
    const ws = currentWeekStart.value
    const we = getWeekEnd(ws)
    const weekNum = getWeekNumber(ws)
    return `第${weekNum}周 (${formatDateShort(ws)} - ${formatDateShort(we)})`
  } else {
    return `${currentMonth.value.year}年${currentMonth.value.month}月`
  }
})

function getWeekNumber(d: Date): number {
  const start = new Date(d.getFullYear(), 0, 1)
  const diff = (d.getTime() - start.getTime()) / 86400000
  return Math.ceil((diff + start.getDay() + 1) / 7)
}

function formatDateShort(d: Date): string {
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function prevPeriod() {
  if (viewMode.value === 'week') {
    currentWeekStart.value = new Date(currentWeekStart.value.getTime() - 7 * 86400000)
  } else {
    if (currentMonth.value.month === 1) {
      currentMonth.value = { year: currentMonth.value.year - 1, month: 12 }
    } else {
      currentMonth.value = { ...currentMonth.value, month: currentMonth.value.month - 1 }
    }
  }
  refreshData()
}

function nextPeriod() {
  if (viewMode.value === 'week') {
    currentWeekStart.value = new Date(currentWeekStart.value.getTime() + 7 * 86400000)
  } else {
    if (currentMonth.value.month === 12) {
      currentMonth.value = { year: currentMonth.value.year + 1, month: 1 }
    } else {
      currentMonth.value = { ...currentMonth.value, month: currentMonth.value.month + 1 }
    }
  }
  refreshData()
}

function onViewModeChange() { refreshData() }
async function refreshData() {
  if (viewMode.value === 'week') {
    store.setFilter('week_start', formatDate(currentWeekStart.value))
    await store.fetch()
    await Promise.all([fetchStats(), fetchTrend(), computeDailyHours()])
  } else {
    delete store.filters.week_start
    await fetchMonthItems()
    await Promise.all([fetchStats(), fetchTrend(), computeDailyHours()])
  }
}

// ── Filters ──
const projectFilter = ref<number | null>(null)
const typeFilter = ref('')

function onProjectFilterChange(val: number | '') {
  store.setFilter('project_id', val || undefined)
}
function onTypeFilterChange(val: string) {
  store.setFilter('type', val || undefined)
}
const tagFilter = ref('')
function onTagFilterChange(val: string) {
  store.setFilter('tag', val || undefined)
}
const allTags = computed(() => {
  const set = new Set<string>()
  store.items.forEach(item => (item.tags || []).forEach(t => set.add(t)))
  return Array.from(set).sort()
})
const searchFilter = ref('')
function onSearchChange() {
  store.setFilter('search', searchFilter.value || undefined)
}
const overdueFilter = ref(false)
function onOverdueFilterChange(val: boolean) {
  store.setFilter('overdue', val || undefined)
}

const priorityFilter = ref('')
function onPriorityFilterChange(val: string) {
  store.setFilter('priority', val || undefined)
}

// ── Sort ──
const sortBy = ref('')
const PRIORITY_ORDER: Record<string, number> = { high: 0, medium: 1, low: 2 }

function onSortChange() {} // triggers computed re-eval via sortBy ref

function _scopeParam(): { target_user_id?: number } {
  return scope.targetUserId !== 0 ? { target_user_id: scope.targetUserId } : {}
}
function _scopeVal(): number | undefined {
  return scope.targetUserId !== 0 ? scope.targetUserId : undefined
}

// ── Weekday filter ──
const weekdayFilter = ref('')
const weekdayOptions = [
  { value: '0', label: '周一' }, { value: '1', label: '周二' }, { value: '2', label: '周三' },
  { value: '3', label: '周四' }, { value: '4', label: '周五' }, { value: '5', label: '周六' }, { value: '6', label: '周日' },
]

function onWeekdayFilterChange() {} // triggers computed re-eval via weekdayFilter ref

// ── Weekday colors (localStorage persisted) ──
const DEFAULT_WEEKDAY_COLORS: Record<string, string> = {
  '0': '#6366f1', '1': '#06b6d4', '2': '#67c23a', '3': '#e6a23c', '4': '#f56c6c', '5': '#8b5cf6', '6': '#909399',
}

const weekdayColors = ref<Record<string, string>>({ ...DEFAULT_WEEKDAY_COLORS })
try {
  const saved = localStorage.getItem('taskflow_weekday_colors')
  if (saved) weekdayColors.value = { ...DEFAULT_WEEKDAY_COLORS, ...JSON.parse(saved) }
} catch {}

function saveWeekdayColors() {
  localStorage.setItem('taskflow_weekday_colors', JSON.stringify(weekdayColors.value))
}

function getWeekdayColor(dateStr: string): string {
  const d = new Date(dateStr)
  const dow = String(d.getDay() === 0 ? 6 : d.getDay() - 1) // 0=Mon..6=Sun
  return weekdayColors.value[dow] || '#909399'
}

function getWeekdayLabel(dateStr: string): string {
  const d = new Date(dateStr)
  const map = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return map[d.getDay() === 0 ? 6 : d.getDay() - 1]
}

function formatDateDisplay(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// ── Work Items (with client-side filtering & sorting) ──
const filteredItems = computed(() => {
  let list = [...store.items]

  // Weekday filter (client-side, week view only)
  if (viewMode.value === 'week' && weekdayFilter.value !== '') {
    const targetDow = parseInt(weekdayFilter.value)
    list = list.filter(item => {
      if (!item.start_date) return false
      const d = new Date(item.start_date)
      const dow = d.getDay() === 0 ? 6 : d.getDay() - 1 // 0=Mon..6=Sun
      return dow === targetDow
    })
  }

  // Sort
  if (sortBy.value === 'date') {
    list.sort((a, b) => {
      if (!a.start_date && !b.start_date) return 0
      if (!a.start_date) return 1
      if (!b.start_date) return -1
      return new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
    })
  } else if (sortBy.value === 'priority') {
    list.sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 2) - (PRIORITY_ORDER[b.priority] ?? 2))
  } else if (sortBy.value === 'date_priority') {
    list.sort((a, b) => {
      // First by date (date only, ignore time)
      const da = a.start_date ? a.start_date.slice(0, 10) : ''
      const db = b.start_date ? b.start_date.slice(0, 10) : ''
      if (da && db && da !== db) return da.localeCompare(db)
      if (da && !db) return -1
      if (!da && db) return 1
      // Then by priority (high → medium → low)
      return (PRIORITY_ORDER[a.priority] ?? 2) - (PRIORITY_ORDER[b.priority] ?? 2)
    })
  }

  return list
})

const groupedItems = computed(() => {
  const map = new Map<number, { projectId: number; projectName: string; projectColor: string; items: WorkItem[] }>()
  for (const item of filteredItems.value) {
    if (!map.has(item.project_id)) {
      const proj = projectStore.projects.find(p => p.id === item.project_id)
      map.set(item.project_id, {
        projectId: item.project_id,
        projectName: proj?.name || `项目#${item.project_id}`,
        projectColor: proj?.color || '#999',
        items: [],
      })
    }
    map.get(item.project_id)!.items.push(item)
  }
  return Array.from(map.values())
})

function getItemHours(itemId: number): number {
  return store.getTotalHours(itemId)
}

function displayItemHours(item: WorkItem): number {
  if (item.is_cross_week && item.week_hours && viewMode.value === 'week') {
    const ws = formatDate(currentWeekStart.value)
    return item.week_hours[ws] ?? item.estimated_hours ?? 0
  }
  return item.estimated_hours ?? 0
}

/** For cross-week items, determine the effective column:
 *  if current week is completed → always "done", else follow item.status */
function getItemCol(item: WorkItem): string {
  if (item.is_cross_week && viewMode.value === 'week') {
    const ws = formatDate(currentWeekStart.value)
    if ((item.completed_weeks || []).includes(ws)) return 'done'
  }
  return item.status
}

function isOverdue(item: WorkItem): boolean {
  if (!item.end_date || getItemCol(item) === 'done') return false
  return new Date() > new Date(item.end_date)
}

// ── Drag and drop ──
let draggedItem: WorkItem | null = null
let dragOverIdx = -1
function onDragStart(e: DragEvent, item: WorkItem) {
  draggedItem = item
  if (e.dataTransfer) { e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', String(item.id)) }
}
function onDragOver(e: DragEvent, idx: number) { e.preventDefault(); dragOverIdx = idx }
function onDragEnd() { draggedItem = null; dragOverIdx = -1 }
async function onDrop(e: DragEvent, toStatus: string, group: any) {
  if (!draggedItem) return
  const itemId = draggedItem.id
  const targetIdx = dragOverIdx >= 0 ? dragOverIdx : group.items.filter((i: WorkItem) => getItemCol(i) === toStatus).length
  const ws = formatDate(currentWeekStart.value)
await store.moveItem(itemId, toStatus, targetIdx, ws)
  // Reload correct dataset based on view mode
  if (viewMode.value === 'week') {
    await store.fetch()
  } else {
    await fetchMonthItems()
  }
  await store.loadLogs(itemId)
  computeDailyHours()
  await fetchStats()
  await fetchTrend()
  ElMessage.success('已移动')
}

// ── Dialog ──
const dialogVisible = ref(false)
const editorRef = ref<any>(null)
const editingItem = ref<WorkItem | null>(null)
const saving = ref(false)
const dialogSaved = ref(false) // skip cleanup on save

async function cleanupOrphanImages(keepUrls: string[]) {
  if (!editorRef.value) return
  const sessionUrls = editorRef.value.getSessionUrls() as string[]
  const keepSet = new Set(keepUrls)
  const orphaned = sessionUrls.filter(u => !keepSet.has(u))
  if (orphaned.length > 0) {
    try { await cleanupWorkImages(orphaned) } catch {}
  }
}

async function cleanupAllSessionImages() {
  if (!editorRef.value) return
  const sessionUrls = editorRef.value.getSessionUrls() as string[]
  if (sessionUrls.length > 0) {
    try { await cleanupWorkImages(sessionUrls) } catch {}
  }
}

// When dialog closes: if not saved, clean up ALL session images & attachments
watch(dialogVisible, (val) => {
  if (!val) {
    if (!dialogSaved.value) {
      cleanupAllSessionImages()
      cleanupAllSessionAttachments()
    }
    dialogSaved.value = false
  }
})
const showLogInput = ref(false)
const editLogId = ref<number | null>(null)
const editLogForm = reactive({ hours: 0, log_date: '', note: '' })

function startAddLog() { showLogInput.value = true; editLogId.value = null }
function cancelAddLog() { showLogInput.value = false; logForm.hours = 1; logForm.note = '' }
function startEditLog(log: any) {
  editLogId.value = log.id
  editLogForm.hours = log.hours
  editLogForm.log_date = log.log_date || ''
  editLogForm.note = log.note || ''
  showLogInput.value = false
}
function cancelEditLog() { editLogId.value = null }
async function saveEditLog(logId: number) {
  if (!editingItem.value || !editLogForm.hours) return
  await store.editLog(logId, editingItem.value.id, {
    hours: editLogForm.hours,
    log_date: editLogForm.log_date || undefined,
    note: editLogForm.note || undefined,
  })
  editLogId.value = null
  store.loadLogs(editingItem.value.id).then(logs => { editingLogs.value = logs })
  refreshStats()
  computeDailyHours()
}

const itemForm = reactive({
  title: '', description: '', project_id: 0, type: 'task', priority: 'medium',
  status: 'todo', estimated_hours: null as number | null,
  start_date: '', end_date: '', tags: [] as string[],
  attachments: [] as AttachItem[],
  week_end: null as string | null,
  week_hours: null as Record<string, number> | null,
})

// Cross-week state
const crossWeekEnabled = ref(false)
const crossWeekStart = ref('')
const crossWeekEnd = ref('')
const weekList = ref<{ key: string; hours: number }[]>([])

function getMondayStr(d: Date): string {
  const date = new Date(d)
  const day = date.getDay()
  const diff = date.getDate() - day + (day === 0 ? -6 : 1)
  date.setDate(diff)
  date.setHours(0, 0, 0, 0)
  return formatDate(date)
}

function disableNonMonday(d: Date): boolean {
  return d.getDay() !== 1
}

function getWeekLabel(key: string): string {
  const d = new Date(key + 'T00:00:00')
  const m = d.getMonth() + 1; const dt = d.getDate()
  return `W${Math.ceil((d.getDate() + 6 - d.getDay()) / 7)} ${m}/${dt}`
}

function buildWeekList(start: string, end: string, existing?: Record<string, number>) {
  const list: { key: string; hours: number }[] = []
  if (!start || !end) return list
  const s = new Date(start + 'T00:00:00')
  const e = new Date(end + 'T00:00:00')
  if (s > e) return list
  const cur = new Date(s)
  while (cur <= e) {
    const key = formatDate(cur)
    list.push({ key, hours: existing?.[key] ?? 0 })
    cur.setDate(cur.getDate() + 7)
  }
  return list
}

// Watch cross-week toggle → clear data when disabled
watch(crossWeekEnabled, (val) => {
  if (!val) {
    itemForm.week_end = null
    itemForm.week_hours = null
    crossWeekStart.value = ''
    crossWeekEnd.value = ''
    weekList.value = []
  }
})

function rebuildWeekHours() {
  if (!crossWeekStart.value || !crossWeekEnd.value) { weekList.value = []; return }
  const existing = { ...itemForm.week_hours } || {}
  weekList.value = buildWeekList(crossWeekStart.value, crossWeekEnd.value, existing)
  syncWeekHours()
}

function syncWeekHours() {
  if (!crossWeekEnabled.value) return
  const wh: Record<string, number> = {}
  for (const w of weekList.value) wh[w.key] = w.hours || 0
  itemForm.week_hours = wh
  itemForm.week_end = crossWeekEnd.value || null
  itemForm.week_start = crossWeekStart.value || itemForm.week_start
  // Auto-compute total estimated_hours
  itemForm.estimated_hours = Object.values(wh).reduce((s, v) => s + (v || 0), 0)
}
const formErrors = reactive({ title: '' })

const logForm = reactive({ hours: 1, log_date: formatDate(new Date()), note: '' })

// Tag input (same pattern as KanbanView)
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref<any>(null)
function showItemTagInput() {
  tagInputVisible.value = true
  nextTick(() => tagInputRef.value?.focus?.())
}
// Attachment helpers
const sessionAttachUrls = new Set<string>()
const attachInput = ref<HTMLInputElement | null>(null)
const attachDragover = ref(false)

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
}

async function uploadAttachFile(file: File) {
  try {
    const res = await uploadAttachApi(file)
    itemForm.attachments.push({ name: res.name, url: res.url, size: res.size })
    sessionAttachUrls.add(res.url)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  }
}

function handleAttachPick(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files) return
  for (const file of files) uploadAttachFile(file)
}

function handleAttachDrop(e: DragEvent) {
  attachDragover.value = false
  const files = e.dataTransfer?.files
  if (!files) return
  for (const file of files) uploadAttachFile(file)
}

function openAttach(url: string) {
  window.open(url, '_blank')
}

function removeAttach(idx: number) {
  const att = itemForm.attachments[idx]
  if (att) {
    // Immediately delete the file from server
    if (att.url) {
      cleanupWorkImages([att.url]).catch(() => {})
      sessionAttachUrls.delete(att.url)
    }
    itemForm.attachments.splice(idx, 1)
  }
}

async function cleanupOrphanAttachments(keepUrls: string[]) {
  const orphaned = [...sessionAttachUrls].filter(u => !keepUrls.includes(u))
  if (orphaned.length > 0) {
    try { await cleanupWorkImages(orphaned) } catch {}
  }
}

async function cleanupAllSessionAttachments() {
  if (sessionAttachUrls.size > 0) {
    try { await cleanupWorkImages([...sessionAttachUrls]) } catch {}
  }
}

function addItemTag() {
  const val = tagInputValue.value.trim()
  if (val && !itemForm.tags.includes(val)) itemForm.tags.push(val)
  tagInputValue.value = ''
  tagInputVisible.value = false
}
const editingLogs = ref<{ id: number; log_date: string | null; hours: number; note: string | null; is_system: boolean }[]>([])

function openCreate() {
  editingItem.value = null
  itemForm.title = ''; itemForm.description = ''; itemForm.project_id = projectStore.projects[0]?.id || 0
  itemForm.type = 'task'; itemForm.priority = 'medium'; itemForm.status = 'todo'
  itemForm.estimated_hours = null; itemForm.start_date = formatDateTime(new Date()); itemForm.end_date = ''
  itemForm.tags = []; itemForm.attachments = []
  itemForm.week_end = null; itemForm.week_hours = null
  crossWeekEnabled.value = false; crossWeekStart.value = ''; crossWeekEnd.value = ''; weekList.value = []
  sessionAttachUrls.clear()
  formErrors.title = ''
  showLogInput.value = false
  editingLogs.value = []
  dialogVisible.value = true
}

function openEdit(item: WorkItem) {
  editingItem.value = item
  itemForm.title = item.title; itemForm.description = item.description || ''
  itemForm.project_id = item.project_id; itemForm.type = item.type
  itemForm.priority = item.priority; itemForm.status = item.status
  itemForm.estimated_hours = item.estimated_hours
  itemForm.start_date = item.start_date ? item.start_date.slice(0, 19) : ''
  itemForm.end_date = item.end_date ? item.end_date.slice(0, 19) : ''
  itemForm.tags = [...(item.tags || [])]
  itemForm.attachments = [...(item.attachments || [])]
  itemForm.week_end = item.week_end || null
  itemForm.week_hours = item.week_hours || null
  // Restore cross-week state
  if (item.is_cross_week && item.week_hours) {
    crossWeekEnabled.value = true
    crossWeekStart.value = item.week_start || ''
    crossWeekEnd.value = item.week_end || ''
    weekList.value = buildWeekList(crossWeekStart.value, crossWeekEnd.value, item.week_hours)
  } else {
    crossWeekEnabled.value = false; crossWeekStart.value = ''; crossWeekEnd.value = ''; weekList.value = []
  }
  sessionAttachUrls.clear()
  formErrors.title = ''
  showLogInput.value = false
  dialogVisible.value = true
  // Load logs and milestones
  store.loadLogs(item.id).then(logs => { editingLogs.value = logs })
  loadMilestones()
}

async function handleSave() {
  if (!itemForm.title.trim()) { formErrors.title = '标题不能为空'; return }
  if (!itemForm.project_id) { ElMessage.warning('请选择项目'); return }
  saving.value = true
  try {
    const data: any = {
      title: itemForm.title, description: itemForm.description,
      project_id: itemForm.project_id, type: itemForm.type, priority: itemForm.priority,
      estimated_hours: itemForm.estimated_hours,
      start_date: itemForm.start_date || undefined,
      end_date: itemForm.end_date || undefined,
      week_start: crossWeekEnabled.value && crossWeekStart.value ? crossWeekStart.value : (viewMode.value === 'week' ? formatDate(currentWeekStart.value) : formatDate(getMonday(new Date(currentMonth.value.year, currentMonth.value.month - 1, 1)))),
      tags: itemForm.tags,
      attachments: itemForm.attachments,
      week_end: crossWeekEnabled.value ? (itemForm.week_end || undefined) : undefined,
      week_hours: crossWeekEnabled.value ? (itemForm.week_hours || undefined) : undefined,
    }
    // If not cross-week, clear the fields
    if (!crossWeekEnabled.value) {
      data.week_end = null
      data.week_hours = null
    }
    if (editingItem.value) {
      data.status = itemForm.status
      await store.update(editingItem.value.id, data)
      ElMessage.success('已更新')
    } else {
      await store.add(data)
      ElMessage.success('已创建')
    }
    // Clean up orphaned session images & attachments before closing dialog
    if (editorRef.value) {
      const currentUrls = editorRef.value.getCurrentImageUrls() as string[]
      await cleanupOrphanImages(currentUrls)
    }
    const currentAttachUrls = itemForm.attachments.map(a => a.url || '').filter(Boolean)
    await cleanupOrphanAttachments(currentAttachUrls)
    dialogSaved.value = true
    dialogVisible.value = false
    refreshData()
  } catch { ElMessage.error('操作失败') }
  finally { saving.value = false }
}

async function handleDelete() {
  if (!editingItem.value) return
  try {
    await ElMessageBox.confirm('确定删除此工作项？', '确认', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' })
    await store.remove(editingItem.value.id)
    dialogVisible.value = false
    refreshData()
    ElMessage.success('已删除')
  } catch {}
}

async function addLogEntry() {
  if (!editingItem.value || !logForm.hours) return
  const ws = viewMode.value === 'week' ? formatDate(currentWeekStart.value) : editingItem.value.week_start || formatDate(getMonday(new Date(currentMonth.value.year, currentMonth.value.month - 1, 1)))
  try {
    await store.addLog({
      work_item_id: editingItem.value.id,
      week_start: ws,
      hours: logForm.hours,
      log_date: logForm.log_date || undefined,
      note: logForm.note || undefined,
    })
    logForm.hours = 1; logForm.note = ''
    showLogInput.value = false
    // Refresh logs
    store.loadLogs(editingItem.value.id).then(logs => { editingLogs.value = logs })
    refreshStats()
    computeDailyHours()
  } catch { ElMessage.error('记录失败') }
}

async function removeLogEntry(logId: number) {
  if (!editingItem.value) return
  await store.removeLog(logId, editingItem.value.id)
  store.loadLogs(editingItem.value.id).then(logs => { editingLogs.value = logs })
  refreshStats()
  computeDailyHours()
}

// ── Milestones ──
const milestones = ref<Milestone[]>([])
const msDialogVisible = ref(false)
const editingMilestone = ref<Milestone | null>(null)
const savingMs = ref(false)
const msForm = reactive({ title: '', description: '', hours: null as number | null, target_date: '', week_start: '' })
const msErrors = reactive({ title: '' })

const milestoneProgress = computed(() => {
  if (!milestones.value.length) return 0
  const done = milestones.value.filter(m => m.is_completed).length
  return Math.round((done / milestones.value.length) * 100)
})
const hasCompletedMs = computed(() => milestones.value.some(m => m.is_completed))
const showClearBtn = computed(() => milestones.value.some(m => m.is_completed && !m.is_locked))
const progressColor = computed(() => {
  const p = milestoneProgress.value
  if (p >= 100) return '#67c23a'
  if (p >= 50) return '#6366f1'
  return '#e6a23c'
})

async function loadMilestones() {
  if (!editingItem.value) return
  milestones.value = await fetchMilestones(editingItem.value.id)
}

function openMilestoneDialog(m?: Milestone) {
  msErrors.title = ''
  if (m) {
    editingMilestone.value = m
    msForm.title = m.title; msForm.description = m.description || ''
    msForm.hours = m.hours; msForm.target_date = m.target_date || ''
    msForm.week_start = m.week_start || ''
  } else {
    editingMilestone.value = null
    msForm.title = ''; msForm.description = ''; msForm.hours = null; msForm.target_date = ''
    // Auto-set week_start to current browsing week
    msForm.week_start = formatDate(currentWeekStart.value)
  }
  msDialogVisible.value = true
}

async function saveMilestone() {
  if (!msForm.title.trim()) { msErrors.title = '标题不能为空'; return }
  if (!editingItem.value) return
  savingMs.value = true
  try {
    const data = {
      title: msForm.title,
      description: msForm.description || undefined,
      hours: msForm.hours || undefined,
      target_date: msForm.target_date || undefined,
      week_start: msForm.week_start || undefined,
    }
    if (editingMilestone.value) {
      await updateMilestone(editingMilestone.value.id, data)
    } else {
      await createMilestone({ work_item_id: editingItem.value.id, ...data })
    }
    msDialogVisible.value = false
    await loadMilestones()
    // Refresh work logs, stats, and daily chart
    if (editingItem.value) {
      await store.loadLogs(editingItem.value.id).then(logs => { editingLogs.value = logs })
      await refreshStats()
      computeDailyHours()
      // Refresh store items so left panel progress bars update
      await store.fetch()
    }
  } catch { ElMessage.error('操作失败') }
  finally { savingMs.value = false }
}

async function toggleMilestone(m: Milestone) {
  await updateMilestone(m.id, { is_completed: !m.is_completed })
  await loadMilestones()
  // Refresh work logs and stats (completion auto-creates/deletes work log)
  if (editingItem.value) {
    await store.loadLogs(editingItem.value.id).then(logs => { editingLogs.value = logs })
    await refreshStats()
    computeDailyHours()
    await store.fetch()
  }
}

async function clearCompletedMilestones() {
  const completed = milestones.value.filter(m => m.is_completed && !m.is_locked)
  if (!completed.length) return
  try {
    await ElMessageBox.confirm(`确定清除 ${completed.length} 个已完成的里程碑？`, '确认', { type: 'warning' })
    for (const m of completed) {
      await deleteMilestone(m.id)
    }
    await loadMilestones()
    if (editingItem.value) {
      await store.loadLogs(editingItem.value.id).then(logs => { editingLogs.value = logs })
      await refreshStats()
      computeDailyHours()
      await store.fetch()
    }
  } catch {}
}

async function removeMilestone(id: number) {
  try {
    await ElMessageBox.confirm('删除此里程碑？', '确认', { type: 'warning' })
    await deleteMilestone(id)
    await loadMilestones()
    // Refresh work logs, stats, and daily chart
    if (editingItem.value) {
      await store.loadLogs(editingItem.value.id).then(logs => { editingLogs.value = logs })
      await refreshStats()
      computeDailyHours()
      await store.fetch()
    }
  } catch {}
}

// Milestone drag-and-drop
const msDragId = ref<number | null>(null)
function onMsDragStart(e: DragEvent, m: Milestone, _idx: number) {
  msDragId.value = m.id
  if (e.dataTransfer) { e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', String(m.id)) }
}
function onMsDragOver(_e: DragEvent, _m: Milestone) {}
function onMsDragEnd() { msDragId.value = null }
async function onMsDrop(e: DragEvent, target: Milestone, targetIdx: number) {
  e.preventDefault()
  if (!msDragId.value || msDragId.value === target.id) return
  const items = [...milestones.value]
  const srcIdx = items.findIndex(x => x.id === msDragId.value)
  if (srcIdx === -1) return
  const [moved] = items.splice(srcIdx, 1)
  items.splice(targetIdx, 0, moved)
  milestones.value = items
  // Persist sort order
  const reorderData = items.map((m, i) => ({ id: m.id, sort_order: i }))
  await reorderMilestones(reorderData)
  msDragId.value = null
}

// ── Project management ──
const showProjectDialog = ref(false)
const newProjectName = ref('')
const newProjectColor = ref('#6366f1')
const editingProjectId = ref<number | null>(null)

async function submitProject() {
  if (!newProjectName.value.trim()) return
  if (editingProjectId.value) {
    await projectStore.update(editingProjectId.value, { name: newProjectName.value.trim(), color: newProjectColor.value })
    ElMessage.success('项目已更新')
  } else {
    await projectStore.add({ name: newProjectName.value.trim(), color: newProjectColor.value })
    ElMessage.success('项目已添加')
  }
  resetProjectForm()
}

function editProject(p: { id: number; name: string; color: string }) {
  editingProjectId.value = p.id
  newProjectName.value = p.name
  newProjectColor.value = p.color
}

function cancelEditProject() {
  resetProjectForm()
}

function resetProjectForm() {
  editingProjectId.value = null
  newProjectName.value = ''
  newProjectColor.value = '#6366f1'
}

async function removeProject(id: number) {
  try {
    await ElMessageBox.confirm('删除项目将同时删除其下所有工作项和工时记录', '确认', { confirmButtonText: '删除', type: 'warning' })
    await projectStore.remove(id)
    ElMessage.success('已删除')
  } catch {}
}

// ── Month view: fetch all items across the month ──
async function fetchMonthItems() {
  const year = currentMonth.value.year
  const month = currentMonth.value.month
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const from = formatDate(getMonday(firstDay))
  const to = formatDate(lastDay)
  // Single range query — no blink
  store.items = await fetchWorkItems({ ...store.filters, week_start_from: from, week_start_to: to, ..._scopeParam() })
}

// ── Stats ──
const currentStats = ref<WeeklyStats | MonthlyStats | null>(null)
const trendData = ref<TrendPoint[]>([])

async function fetchStats() {
  if (viewMode.value === 'week') {
    currentStats.value = await getWeeklyStats(formatDate(currentWeekStart.value), _scopeVal())
    // Also fetch notes for the current week
    try {
      const t = await getWeeklyTarget(formatDate(currentWeekStart.value))
      currentNotes.value = t.notes || ''
    } catch { currentNotes.value = '' }
  } else {
    currentStats.value = await getMonthlyStats(currentMonth.value.year, currentMonth.value.month, _scopeVal())
    // Fetch notes for the first week of the month
    try {
      const ws = formatDate(getMonday(new Date(currentMonth.value.year, currentMonth.value.month - 1, 1)))
      const t = await getWeeklyTarget(ws)
      currentNotes.value = t.notes || ''
    } catch { currentNotes.value = '' }
  }
}
async function fetchTrend() { trendData.value = await getTrendStats(12, _scopeVal()) }
function refreshStats() { fetchStats() }

// ── Export ──
function handleExport() {
  const itemHoursMap = new Map<number, number>()
  for (const item of store.items) {
    itemHoursMap.set(item.id, store.getTotalHours(item.id))
  }

  const projectNameMap = new Map<number, string>()
  for (const p of projectStore.projects) {
    projectNameMap.set(p.id, p.name)
  }

  exportWorkWeekly({
    periodLabel: periodLabel.value,
    viewMode: viewMode.value,
    items: filteredItems.value,
    projectNameMap,
    itemHoursMap,
    currentStats: currentStats.value,
    trendData: trendData.value,
  })
}

// ── Custom target ──
const targetDialogVisible = ref(false)
const targetFormHours = ref(40)
const targetFormNotes = ref('')
const currentNotes = ref('')

function openTargetDialog() {
  targetFormHours.value = currentStats.value?.weekly_target || currentStats.value?.monthly_target || 40
  targetFormNotes.value = currentNotes.value || ''
  targetDialogVisible.value = true
}

async function saveTarget() {
  try {
    if (viewMode.value === 'week') {
      const ws = formatDate(currentWeekStart.value)
      await setWeeklyTarget(ws, targetFormHours.value, targetFormNotes.value || undefined)
      ElMessage.success(`已设置目标为 ${targetFormHours.value}h`)
    } else {
      const y = currentMonth.value.year, m = currentMonth.value.month
      let d = getMonday(new Date(y, m - 1, 1))
      const lastDay = new Date(y, m, 0)
      while (d <= lastDay) {
        await setWeeklyTarget(formatDate(d), targetFormHours.value, targetFormNotes.value || undefined)
        d = new Date(d.getTime() + 7 * 86400000)
      }
      ElMessage.success(`已设置目标为 ${targetFormHours.value}h`)
    }
    targetDialogVisible.value = false
    await Promise.all([fetchStats(), fetchTrend()])
  } catch { ElMessage.error('保存失败') }
}

async function resetTarget() {
  try {
    if (viewMode.value === 'week') {
      await setWeeklyTarget(formatDate(currentWeekStart.value), 40, '')
      ElMessage.success('已恢复默认 40h')
    }
    targetDialogVisible.value = false
    await Promise.all([fetchStats(), fetchTrend()])
  } catch { ElMessage.error('操作失败') }
}

// Daily breakdown by weekday (Mon-Sun) — based on work item estimated_hours + start_date
const dailyHours = ref<number[]>([0, 0, 0, 0, 0, 0, 0])

function computeDailyHours() {
  const hours = [0, 0, 0, 0, 0, 0, 0]
  for (const item of store.items) {
    const eh = displayItemHours(item)
    if (!eh || !item.start_date) continue
    const d = new Date(item.start_date)
    const dow = d.getDay() === 0 ? 6 : d.getDay() - 1 // 0=Mon..6=Sun
    if (dow >= 0 && dow < 7) hours[dow] += eh
  }
  dailyHours.value = hours.map(h => Math.round(h * 10) / 10)
}

// ── Chart options ──
const saturationOption = computed(() => {
  const pct = currentStats.value?.saturation_pct || 0
  const color = pct >= 100 ? '#67c23a' : pct >= 70 ? '#6366f1' : '#e6a23c'
  return {
    series: [{
      type: 'pie',
      radius: ['68%', '88%'],
      center: ['50%', '50%'],
      silent: true,
      labelLine: { show: false },
      label: { show: true, position: 'center', formatter: `{p|${pct}%}\n{r|饱和度}`, rich: { p: { fontSize: 28, fontWeight: 800, color: chart.textPrimary.value }, r: { fontSize: 12, color: chart.textSecondary.value, lineHeight: 22 } } },
      data: [
        { value: pct, name: '已用', itemStyle: { color, borderRadius: 6, borderColor: chart.bgColor.value, borderWidth: 2 } },
        { value: Math.max(0, 100 - pct), name: '剩余', itemStyle: { color: chart.fillLight.value, borderRadius: 6, borderColor: chart.bgColor.value, borderWidth: 2 } },
      ],
    }],
  }
})

const projectBarOption = computed(() => {
  const data = currentStats.value?.project_breakdown || []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '12%', bottom: '3%', top: '5%', containLabel: true },
    xAxis: { type: 'value', axisLabel: { fontSize: 11, color: chart.textSecondary.value }, splitLine: { lineStyle: { color: chart.borderLighter.value } } },
    yAxis: { type: 'category', data: data.map(d => d.project_name).reverse(), axisLabel: { fontSize: 12, fontWeight: 600, color: chart.textRegular.value }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar',
      data: data.map(d => ({ value: d.hours, itemStyle: { color: d.project_color, borderRadius: [0, 6, 6, 0] } })).reverse(),
      barWidth: 16,
      label: { show: true, position: 'right', fontSize: 12, fontWeight: 600, color: chart.textRegular.value, formatter: '{c}h' },
    }],
  }
})

// Daily hours bar chart (Mon-Sun)
const WEEKDAY_LABELS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const WEEKDAY_COLORS = ['#6366f1', '#06b6d4', '#67c23a', '#e6a23c', '#f56c6c', '#8b5cf6', '#909399']
const dailyBarOption = computed(() => ({
  tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].name}: ${p[0].value}h` },
  grid: { left: '3%', right: '8%', bottom: '3%', top: '8%', containLabel: true },
  xAxis: { type: 'category', data: WEEKDAY_LABELS, axisLabel: { color: chart.textSecondary.value, fontSize: 11 } },
  yAxis: { type: 'value', axisLabel: { color: chart.textSecondary.value, formatter: '{value}h' }, splitLine: { lineStyle: { type: 'dashed', color: chart.borderLight.value } } },
  series: [{
    type: 'bar',
    data: dailyHours.value.map((h, i) => ({ value: h, itemStyle: { color: WEEKDAY_COLORS[i], borderRadius: [6, 6, 0, 0] } })),
    barWidth: 28,
    label: { show: true, position: 'top', fontSize: 11, fontWeight: 600, color: chart.textRegular.value, formatter: (p: any) => p.value > 0 ? p.value + 'h' : '' },
  }],
}))

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '5%', bottom: '5%', top: '8%', containLabel: true },
  xAxis: {
    type: 'category',
    data: trendData.value.map(d => d.week_start.slice(5)),
    axisLabel: { fontSize: 11, color: chart.textSecondary.value, rotate: 45 },
  },
  yAxis: { type: 'value', min: 0, axisLabel: { fontSize: 11, color: chart.textSecondary.value }, splitLine: { lineStyle: { color: chart.borderLighter.value } } },
  series: [{
    type: 'line',
    data: trendData.value.map(d => d.total_hours),
    smooth: true,
    lineStyle: { color: '#6366f1', width: 3 },
    itemStyle: { color: '#6366f1' },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(99,102,241,0.25)' }, { offset: 1, color: 'rgba(99,102,241,0.02)' }] } },
    symbol: 'circle', symbolSize: 6,
    markLine: { silent: true, data: [{ yAxis: 40, label: { formatter: '40h 饱和线', fontSize: 10 }, lineStyle: { color: '#e6a23c', type: 'dashed' } }] },
  }],
}))

// ── Init ──
// Auto-preload all work logs whenever items change (drag, filter, page load)
watch(() => store.items, async (newItems) => {
  const raw = toRaw(newItems)
  for (const item of raw) {
    await store.loadLogs(item.id)
  }
  computeDailyHours()
}, { deep: false, immediate: true })

onMounted(async () => {
  await projectStore.fetch()
  await refreshData()
})
</script>

<style scoped>
/* Period navigator */
.period-nav {
  display: flex;
  align-items: center;
  gap: 2px;
}
.period-nav-btn {
  width: 38px; height: 38px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.period-nav-btn:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.period-nav-label {
  font-size: 15px; font-weight: 700;
  min-width: 200px; text-align: center;
  color: var(--el-text-color-primary);
  padding: 0 6px;
}

/* View toggle */
.view-toggle {
  display: flex;
  background: var(--el-fill-color-light);
  border-radius: 10px;
  padding: 3px;
  margin-left: 12px;
}
.view-toggle-btn {
  padding: 7px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  background: transparent;
  color: var(--el-text-color-secondary);
  transition: all 0.25s;
  white-space: nowrap;
}
.view-toggle-btn:hover {
  color: var(--el-color-primary);
}
.view-toggle-btn.active {
  background: var(--el-bg-color);
  color: #6366f1;
  box-shadow: var(--el-box-shadow-light);
}

.ww-toolbar :deep(.el-input__wrapper),
.ww-toolbar :deep(.el-select__wrapper) {
  border-radius: 8px;
}
.ww-toolbar :deep(.el-button) {
  border-radius: 8px;
}
.ww-dialog :deep(.el-input__wrapper),
.ww-dialog :deep(.el-select__wrapper),
.ww-dialog :deep(.el-textarea__inner) {
  border-radius: 8px;
}
.ww-dialog :deep(.el-button) {
  border-radius: 8px;
}

/* Attachment drop zone */
.attach-drop-zone {
  width: 100%;
  height: 56px;
  border: 2px dashed var(--el-border-color);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--el-fill-color-lighter);
}
.attach-drop-zone:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.attach-dragover {
  border-color: var(--el-color-primary) !important;
  color: var(--el-color-primary) !important;
  background: var(--el-color-primary-light-9) !important;
}
.ms-add-btn {
  background: var(--el-color-primary-light-9) !important;
  color: var(--el-color-primary) !important;
  border: none !important;
  border-radius: 6px !important;
}
.ms-add-btn:hover {
  background: var(--el-color-primary) !important;
  color: #fff !important;
}
.ms-clear-btn {
  background: var(--el-color-danger-light-9) !important;
  color: var(--el-color-danger) !important;
  border: none !important;
  border-radius: 6px !important;
}
.ms-clear-btn:hover {
  background: var(--el-color-danger) !important;
  color: #fff !important;
}

/* Weekday filter buttons */
.ww-wd-btn {
  padding: 4px 14px;
  border: 1px solid var(--el-border-color);
  border-radius: 16px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
  white-space: nowrap;
}
.ww-wd-btn:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-3);
  background: var(--el-color-primary-light-9);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--el-color-primary-light-3);
}
.ww-wd-btn--active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.25);
}
.ww-wd-btn--active:hover {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}
</style>
