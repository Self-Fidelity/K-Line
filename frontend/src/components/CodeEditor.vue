<template>
  <div class="code-editor-container" ref="editorContainer" :style="{ height: height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, toRefs } from 'vue'
import { EditorView, basicSetup } from 'codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorState, Compartment } from '@codemirror/state'
import { keymap, ViewUpdate, placeholder as placeholderExt } from '@codemirror/view'
import { indentWithTab } from '@codemirror/commands'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  height: {
    type: String,
    default: '400px'
  },
  darkMode: {
    type: Boolean,
    default: false
  },
  readonly: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const editorContainer = ref<HTMLElement | null>(null)
let editorView: EditorView | null = null

// Theme compartment to switch themes
const themeCompartment = new Compartment()
// Readonly compartment
const readonlyCompartment = new Compartment()

// Init editor
onMounted(() => {
  if (!editorContainer.value) return

  const extensions = [
    basicSetup,
    python(),
    keymap.of([indentWithTab]),
    themeCompartment.of(props.darkMode ? oneDark : []),
    readonlyCompartment.of(EditorState.readOnly.of(props.readonly)),
    EditorView.updateListener.of((update: ViewUpdate) => {
      if (update.docChanged) {
        const newValue = update.state.doc.toString()
        emit('update:modelValue', newValue)
        emit('change', newValue)
      }
    })
  ]

  if (props.placeholder) {
    extensions.push(placeholderExt(props.placeholder))
  }

  editorView = new EditorView({
    doc: props.modelValue,
    extensions: extensions,
    parent: editorContainer.value
  })
})

// Watch for external value changes
watch(() => props.modelValue, (newValue) => {
  if (editorView && newValue !== editorView.state.doc.toString()) {
    editorView.dispatch({
      changes: {
        from: 0,
        to: editorView.state.doc.length,
        insert: newValue
      }
    })
  }
})

// Watch for theme changes
watch(() => props.darkMode, (newVal) => {
  if (editorView) {
    editorView.dispatch({
      effects: themeCompartment.reconfigure(newVal ? oneDark : [])
    })
  }
})

// Watch for readonly changes
watch(() => props.readonly, (newVal) => {
  if (editorView) {
    editorView.dispatch({
      effects: readonlyCompartment.reconfigure(EditorState.readOnly.of(newVal))
    })
  }
})

onBeforeUnmount(() => {
  if (editorView) {
    editorView.destroy()
  }
})
</script>

<style scoped>
.code-editor-container {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  font-size: 14px;
}

:deep(.cm-editor) {
  height: 100%;
}

:deep(.cm-scroller) {
  overflow: auto;
}

/* Light theme adjustments */
:deep(.cm-editor.cm-light) {
  background-color: #fafafa;
}

:deep(.cm-editor.cm-focused) {
  outline: none;
}
</style>
