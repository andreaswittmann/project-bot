import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import api from './services/api'

import './assets/main.css'

// v-md-editor: CodeMirror build + theme + code highlight
import VMdEditor from '@kangc/v-md-editor/lib/codemirror-editor'
import '@kangc/v-md-editor/lib/style/codemirror-editor.css'
import Codemirror from 'codemirror'
import 'codemirror/lib/codemirror.css'
import 'codemirror/mode/markdown/markdown.js'
import 'codemirror/addon/selection/active-line.js'
// Needed because v-md-editor sets scrollbarStyle: 'simple'
import 'codemirror/addon/scroll/simplescrollbars.js'
import 'codemirror/addon/scroll/simplescrollbars.css'
import vuepressTheme from '@kangc/v-md-editor/lib/theme/vuepress'
import '@kangc/v-md-editor/lib/theme/style/vuepress.css'
import enUS from '@kangc/v-md-editor/lib/lang/en-US'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const app = createApp(App)
const pinia = createPinia()

// Configure v-md-editor (CodeMirror build) globally
VMdEditor.Codemirror = Codemirror
VMdEditor.use(vuepressTheme, { Hljs: hljs })
VMdEditor.lang.use('en-US', enUS)

app.use(pinia)
app.use(router)
app.use(VMdEditor) // register <v-md-editor> globally

// Make API service available globally
app.config.globalProperties.$api = api

app.mount('#app')