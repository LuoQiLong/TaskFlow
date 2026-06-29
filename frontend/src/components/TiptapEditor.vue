<template>
  <div class="tiptap-wrapper">
    <!-- Toolbar -->
    <div class="tiptap-toolbar" v-if="editor">
      <!-- Heading -->
      <button type="button" @click="editor.chain().focus().toggleHeading({level:2}).run()" :class="{active:editor.isActive('heading',{level:2})}" title="标题2">H2</button>
      <button type="button" @click="editor.chain().focus().toggleHeading({level:3}).run()" :class="{active:editor.isActive('heading',{level:3})}" title="标题3">H3</button>
      <span class="tiptap-sep"></span>
      <!-- Inline format -->
      <button type="button" @click="editor.chain().focus().toggleBold().run()" :class="{active:editor.isActive('bold')}" title="加粗 Ctrl+B"><b>B</b></button>
      <button type="button" @click="editor.chain().focus().toggleItalic().run()" :class="{active:editor.isActive('italic')}" title="斜体 Ctrl+I"><i>I</i></button>
      <button type="button" @click="editor.chain().focus().toggleStrike().run()" :class="{active:editor.isActive('strike')}" title="删除线"><s>S</s></button>
      <button type="button" @click="editor.chain().focus().toggleUnderline().run()" :class="{active:editor.isActive('underline')}" title="下划线 Ctrl+U"><u>U</u></button>
      <button type="button" @click="editor.chain().focus().toggleCode().run()" :class="{active:editor.isActive('code')}" title="行内代码">&lt;/&gt;</button>
      <button type="button" @click="editor.chain().focus().toggleSuperscript().run()" :class="{active:editor.isActive('superscript')}" title="上标">x²</button>
      <button type="button" @click="editor.chain().focus().toggleSubscript().run()" :class="{active:editor.isActive('subscript')}" title="下标">x₂</button>
      <span class="tiptap-sep"></span>
      <!-- Color & Highlight -->
      <div class="tiptap-color-btn" title="文字颜色">
        <input type="color" @input="editor.chain().focus().setColor(($event.target as HTMLInputElement).value).run()" :value="editor.getAttributes('textStyle').color || '#000000'" />
        <span>A</span>
      </div>
      <button type="button" @click="editor.chain().focus().toggleHighlight().run()" :class="{active:editor.isActive('highlight')}" title="高亮背景">🖌</button>
      <button type="button" @click="editor.chain().focus().unsetColor().run()" v-if="editor.isActive('textStyle')" title="清除颜色">✕</button>
      <span class="tiptap-sep"></span>
      <!-- Align -->
      <button type="button" @click="editor.chain().focus().setTextAlign('left').run()" :class="{active:editor.isActive({textAlign:'left'})}" title="左对齐">⫷</button>
      <button type="button" @click="editor.chain().focus().setTextAlign('center').run()" :class="{active:editor.isActive({textAlign:'center'})}" title="居中">≣</button>
      <button type="button" @click="editor.chain().focus().setTextAlign('right').run()" :class="{active:editor.isActive({textAlign:'right'})}" title="右对齐">⫸</button>
      <span class="tiptap-sep"></span>
      <!-- Lists -->
      <button type="button" @click="editor.chain().focus().toggleBulletList().run()" :class="{active:editor.isActive('bulletList')}" title="无序列表">•≡</button>
      <button type="button" @click="editor.chain().focus().toggleOrderedList().run()" :class="{active:editor.isActive('orderedList')}" title="有序列表">1.</button>
      <button type="button" @click="editor.chain().focus().toggleTaskList().run()" :class="{active:editor.isActive('taskList')}" title="任务列表">☑</button>
      <span class="tiptap-sep"></span>
      <!-- Blocks -->
      <button type="button" @click="editor.chain().focus().toggleBlockquote().run()" :class="{active:editor.isActive('blockquote')}" title="引用">❝</button>
      <button type="button" @click="editor.chain().focus().toggleCodeBlock().run()" :class="{active:editor.isActive('codeBlock')}" title="代码块">{ }</button>
      <button type="button" @click="editor.chain().focus().setHorizontalRule().run()" title="分隔线">—</button>
      <span class="tiptap-sep"></span>
      <!-- Table -->
      <button type="button" @click="insertTable" title="插入表格 (3×3)">▦</button>
      <button type="button" @click="editor.chain().focus().addColumnBefore().run()" title="左插列">◀┆</button>
      <button type="button" @click="editor.chain().focus().addColumnAfter().run()" title="右插列">┆▶</button>
      <button type="button" @click="editor.chain().focus().addRowBefore().run()" title="上插行">▲━</button>
      <button type="button" @click="editor.chain().focus().addRowAfter().run()" title="下插行">━▼</button>
      <button type="button" @click="editor.chain().focus().deleteTable().run()" title="删除表格">✕▦</button>
      <span class="tiptap-sep"></span>
      <!-- Link -->
      <button type="button" @click="setLink" :class="{active:editor.isActive('link')}" title="插入链接">🔗</button>
      <button type="button" @click="editor.chain().focus().unsetLink().run()" :disabled="!editor.isActive('link')" title="取消链接">✂</button>
      <span class="tiptap-sep"></span>
      <!-- Undo/Redo -->
      <button type="button" @click="editor.chain().focus().undo().run()" title="撤销">↩</button>
      <button type="button" @click="editor.chain().focus().redo().run()" title="重做">↪</button>
    </div>
    <!-- Editor content -->
    <editor-content :editor="editor" />
  </div>
</template>

<script setup lang="ts">
import { watch, onBeforeUnmount, nextTick, onMounted } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'
import TextAlign from '@tiptap/extension-text-align'
import { TextStyle } from '@tiptap/extension-text-style'
import Color from '@tiptap/extension-color'
import Highlight from '@tiptap/extension-highlight'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import Superscript from '@tiptap/extension-superscript'
import Subscript from '@tiptap/extension-subscript'
import { Table } from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import { ElMessageBox } from 'element-plus'
import client from '@/api/client'

const props = defineProps<{ modelValue: string; uploadUrl?: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

// Track all image URLs uploaded during this editing session
const sessionUrls = new Set<string>()

function getCurrentImageUrls(): string[] {
  if (!editor.value) return []
  const html = editor.value.getHTML()
  const m = html.matchAll(/\/static\/(work|task)-images\/[^\s"'<>]+/g)
  return [...m].map(x => x[0])
}

function getSessionUrls(): string[] { return [...sessionUrls] }

defineExpose({ getSessionUrls, getCurrentImageUrls })

const editor = useEditor({
  content: props.modelValue || '<p></p>',
  extensions: [
    StarterKit.configure({ heading: { levels: [2, 3] } }),
    Image.configure({ inline: true, allowBase64: false }),
    Placeholder.configure({ placeholder: '描述（可选），支持 Ctrl+V 粘贴图片，支持 Markdown 快捷输入' }),
    Underline,
    Link.configure({ openOnClick: false, HTMLAttributes: { target: '_blank', rel: 'noopener' } }),
    TextStyle,
    Color,
    Highlight.configure({ multicolor: true }),
    TextAlign.configure({ types: ['heading', 'paragraph'] }),
    TaskList,
    TaskItem.configure({ nested: true }),
    Superscript,
    Subscript,
    Table.configure({ resizable: true }),
    TableRow,
    TableCell,
    TableHeader,
  ],
  onUpdate: ({ editor: ed }: any) => emit('update:modelValue', ed.getHTML()),
})

function setLink() {
  if (!editor.value) return
  const prev = editor.value.getAttributes('link').href || ''
  ElMessageBox.prompt('请输入链接地址', '插入链接', {
    confirmButtonText: '确定', cancelButtonText: '取消',
    inputValue: prev, inputPlaceholder: 'https://...',
  }).then(({ value }: any) => {
    if (value) editor.value!.chain().focus().extendMarkRange('link').setLink({ href: value }).run()
    else editor.value!.chain().focus().extendMarkRange('link').unsetLink().run()
  }).catch(() => {})
}

function insertTable() {
  editor.value?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
}

// Paste / drop → upload image
onMounted(() => {
  nextTick(() => {
    const dom = (editor.value as any)?.view?.dom as HTMLElement | undefined
    if (!dom) return
    const onPaste = (event: ClipboardEvent) => {
      const items = event.clipboardData?.items
      if (!items) return
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          event.preventDefault(); event.stopPropagation()
          const file = item.getAsFile()
          if (file) uploadAndInsert(file)
          return
        }
      }
    }
    const onDrop = (event: DragEvent) => {
      const files = event.dataTransfer?.files
      if (!files) return
      for (const file of files) {
        if (file.type.startsWith('image/')) {
          event.preventDefault(); event.stopPropagation()
          uploadAndInsert(file)
          return
        }
      }
    }
    // Click image → open full size in new tab
    const onClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (target.tagName === 'IMG') {
        const src = target.getAttribute('src')
        if (src) window.open(src, '_blank')
      }
    }
    dom.addEventListener('paste', onPaste)
    dom.addEventListener('drop', onDrop)
    dom.addEventListener('click', onClick)
    ;(dom as any)._onPaste = onPaste
    ;(dom as any)._onDrop = onDrop
    ;(dom as any)._onClick = onClick
  })
})

onBeforeUnmount(() => {
  try {
    const dom = (editor.value as any)?.view?.dom as HTMLElement | undefined
    if (dom) {
      if ((dom as any)._onPaste) dom.removeEventListener('paste', (dom as any)._onPaste)
      if ((dom as any)._onDrop) dom.removeEventListener('drop', (dom as any)._onDrop)
      if ((dom as any)._onClick) dom.removeEventListener('click', (dom as any)._onClick)
      if ((dom as any)._onDrop) dom.removeEventListener('drop', (dom as any)._onDrop)
    }
  } catch {}
  editor.value?.destroy()
})

async function uploadAndInsert(file: File) {
  if (!editor.value) return
  const form = new FormData()
  form.append('file', file)
  const uploadPath = props.uploadUrl || '/work-items/upload-image'
  try {
    const res = await client.post(uploadPath, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    sessionUrls.add(res.data.url)
    editor.value.chain().focus().setImage({ src: res.data.url }).run()
  } catch (e: any) {
    import('element-plus').then(m => m.ElMessage.error(e?.response?.data?.detail || '图片上传失败'))
  }
}

watch(() => props.modelValue, (val) => {
  if (editor.value) {
    const html = editor.value.getHTML()
    if (html !== val) editor.value.commands.setContent(val || '<p></p>', true)
  }
})
</script>

<style>
.tiptap-wrapper {
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
  background: var(--el-fill-color-blank);
  transition: border-color 0.2s;
  overflow: hidden;
}
.tiptap-wrapper:hover { border-color: var(--el-border-color-hover); }
.tiptap-wrapper:focus-within { border-color: var(--el-color-primary); }

/* Toolbar */
.tiptap-toolbar {
  display: flex; align-items: center; gap: 1px;
  padding: 5px 8px; flex-wrap: wrap;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}
.tiptap-toolbar button {
  min-width: 28px; height: 28px;
  border: none; border-radius: 4px;
  background: transparent; color: var(--el-text-color-regular);
  cursor: pointer; font-size: 13px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 5px; transition: background 0.15s; white-space: nowrap;
}
.tiptap-toolbar button:hover:not(:disabled) { background: var(--el-fill-color); }
.tiptap-toolbar button.active { background: var(--el-color-primary-light-9); color: var(--el-color-primary); }
.tiptap-toolbar button:disabled { opacity: 0.3; cursor: default; }
.tiptap-sep { width: 1px; height: 18px; background: var(--el-border-color-light); margin: 0 3px; flex-shrink: 0; }

/* Color picker button */
.tiptap-color-btn {
  position: relative; width: 32px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; border-radius: 4px;
}
.tiptap-color-btn:hover { background: var(--el-fill-color); }
.tiptap-color-btn input[type="color"] {
  position: absolute; inset: 0; width: 100%; height: 100%;
  opacity: 0; cursor: pointer; border: none; padding: 0;
}
.tiptap-color-btn span {
  font-size: 14px; font-weight: 700;
  color: var(--el-text-color-regular); pointer-events: none;
}

/* Editor content */
.tiptap-wrapper .ProseMirror {
  padding: 10px 14px; min-height: 200px; max-height: 460px;
  overflow-y: auto; outline: none;
  font-size: var(--el-font-size-base); line-height: 1.7;
  color: var(--el-text-color-primary);
}
.tiptap-wrapper .ProseMirror p.is-editor-empty:first-child::before {
  content: attr(data-placeholder); float: left;
  color: var(--el-text-color-placeholder); pointer-events: none; height: 0;
}
.tiptap-wrapper .ProseMirror img {
  max-width: 100%; height: auto; border-radius: 6px; margin: 6px 0; display: block;
  cursor: pointer;
}
.tiptap-wrapper .ProseMirror img:hover {
  outline: 2px solid var(--el-color-primary); outline-offset: 1px;
}
.tiptap-wrapper .ProseMirror p { margin: 0 0 6px 0; }
.tiptap-wrapper .ProseMirror p:last-child { margin-bottom: 0; }
.tiptap-wrapper .ProseMirror h2 { font-size: 18px; font-weight: 700; margin: 14px 0 6px; line-height: 1.3; }
.tiptap-wrapper .ProseMirror h3 { font-size: 15px; font-weight: 600; margin: 12px 0 4px; line-height: 1.3; }
.tiptap-wrapper .ProseMirror ul,
.tiptap-wrapper .ProseMirror ol { padding-left: 22px; margin: 6px 0; }
.tiptap-wrapper .ProseMirror li { margin-bottom: 3px; }
.tiptap-wrapper .ProseMirror blockquote {
  border-left: 3px solid var(--el-color-primary); padding-left: 14px;
  margin: 10px 0; color: var(--el-text-color-secondary);
}
.tiptap-wrapper .ProseMirror pre {
  background: var(--el-fill-color-light); border-radius: 6px;
  padding: 12px 14px; margin: 10px 0;
  font-family: 'Cascadia Code','Fira Code',monospace; font-size: 13px;
  line-height: 1.5; overflow-x: auto;
}
.tiptap-wrapper .ProseMirror code {
  background: var(--el-fill-color-light); padding: 1px 5px;
  border-radius: 3px; font-family: 'Cascadia Code','Fira Code',monospace; font-size: 0.9em;
}
.tiptap-wrapper .ProseMirror pre code { background: none; padding: 0; }
.tiptap-wrapper .ProseMirror hr { border: none; border-top: 1px solid var(--el-border-color-light); margin: 14px 0; }
.tiptap-wrapper .ProseMirror a { color: var(--el-color-primary); text-decoration: underline; }
.tiptap-wrapper .ProseMirror mark { background: #fff3cd; padding: 0 2px; border-radius: 2px; }

/* Task list */
.tiptap-wrapper .ProseMirror ul[data-type="taskList"] { list-style: none; padding-left: 4px; }
.tiptap-wrapper .ProseMirror ul[data-type="taskList"] li { display: flex; align-items: flex-start; gap: 6px; }
.tiptap-wrapper .ProseMirror ul[data-type="taskList"] li > label { flex-shrink: 0; margin-top: 2px; }

/* Table */
.tiptap-wrapper .ProseMirror table { border-collapse: collapse; width: 100%; margin: 10px 0; }
.tiptap-wrapper .ProseMirror th,
.tiptap-wrapper .ProseMirror td { border: 1px solid var(--el-border-color); padding: 6px 10px; min-width: 40px; }
.tiptap-wrapper .ProseMirror th { background: var(--el-fill-color-light); font-weight: 600; }
</style>
