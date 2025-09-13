<template>
  <div id="app">
    <!-- 文件路径输入 -->
    <div class="header">
      <div class="container">
        <div class="file-input-section">
          <input
            v-model="filePath"
            type="text"
            class="file-input"
            placeholder="请输入CSV文件路径，例如：C:\\path\\to\\unmarked_dataset.csv"
          />
          <button @click="loadFile" class="btn btn-primary" :disabled="loading">
            {{ loading ? '加载中...' : '加载文件' }}
          </button>
        </div>

        <!-- 错误和成功消息 -->
        <div v-if="errorMessage" class="error-message">
          <pre>{{ errorMessage }}</pre>
        </div>
        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>
      </div>
    </div>

    <div class="container" v-if="fileLoaded">
      <!-- 输入文本区域 -->
      <div class="input-section">
        <h3>输入文本</h3>
        <textarea
          v-model="currentRow.input"
          class="input-textarea"
          placeholder="当前样本的输入文本"
          @input="markAsModified"
        ></textarea>
      </div>

      <!-- 标注控制 -->
      <div class="controls-section">
        <div class="controls-grid">
          <div class="control-group">
            <label class="control-label">是否合理</label>
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="currentRow.is_reasonable"
                @change="markAsModified"
              />
              <span class="slider"></span>
            </label>
          </div>

          <div class="control-group">
            <label class="control-label">已标注</label>
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="currentRow.is_annotated"
                @change="markAsModified"
              />
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- 导航和保存 -->
        <div class="navigation-controls">
          <button @click="previousRow" class="btn btn-secondary" :disabled="currentIndex <= 0">
            上一条
          </button>

          <span class="progress-info">
            {{ currentIndex + 1 }} / {{ totalRows }} 
            (已标注: {{ progress.annotated }}, 合理: {{ progress.reasonable }})
          </span>

          <button @click="nextRow" class="btn btn-secondary" :disabled="currentIndex >= totalRows - 1">
            下一条
          </button>

          <button
            @click="saveRow"
            class="btn btn-success"
            :disabled="!hasModifications || saving"
          >
            {{ saving ? '保存中...' : '保存' }}
          </button>

          <button
            @click="autoFixScenegraph"
            class="btn btn-warning"
            :disabled="saving"
          >
            自动修复Scenegraph
          </button>
        </div>
      </div>

      <!-- 可视化区域 -->
      <div class="visualization-section">
        <h3>场景图可视化</h3>
        <div class="full-visualization">
          <div ref="graphContainer" class="graph-container"></div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loading" class="loading">
      正在加载文件...
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, nextTick } from 'vue'
import axios from 'axios'

export default {
  name: 'App',
  setup() {
    const filePath = ref(localStorage.getItem('lastFilePath') || '')
    const fileLoaded = ref(false)
    const loading = ref(false)
    const saving = ref(false)
    const errorMessage = ref('')
    const successMessage = ref('')
    const hasModifications = ref(false)

    const currentRow = reactive({
      id: '',
      input: '',
      scenegraph: '[]',
      is_reasonable: false,
      is_annotated: false
    })

    const currentIndex = ref(0)
    const totalRows = ref(0)
    const progress = reactive({
      total: 0,
      annotated: 0,
      reasonable: 0
    })
    const graphContainer = ref(null)

    const api = axios.create({
      baseURL: '/api',
      timeout: 10000
    })

    const showError = (msg) => {
      errorMessage.value = msg
      successMessage.value = ''
      setTimeout(() => errorMessage.value = '', 10000)
    }
    const showSuccess = (msg) => {
      successMessage.value = msg
      errorMessage.value = ''
      setTimeout(() => successMessage.value = '', 3000)
    }

    const markAsModified = () => {
      hasModifications.value = true
    }

    const loadFile = async () => {
      if (!filePath.value.trim()) return showError('请输入文件路径')
      loading.value = true
      try {
        const res = await api.post('/open', { path: filePath.value })
        if (res.data.success) {
          fileLoaded.value = true
          totalRows.value = res.data.total_rows
          localStorage.setItem('lastFilePath', filePath.value)
          await loadRowByIndex(0)
          await loadProgress()
          showSuccess(`成功加载文件，共 ${totalRows.value} 行数据`)
        }
      } catch (e) {
        showError(e.response?.data?.error || '加载文件失败')
      } finally {
        loading.value = false
      }
    }

    const loadRowByIndex = async (index) => {
      try {
        const res = await api.get(`/row?index=${index}`)
        Object.assign(currentRow, res.data)
        currentIndex.value = index
        hasModifications.value = false
        await nextTick()
        renderGraph()
      } catch (e) {
        showError(e.response?.data?.error || '加载行数据失败')
      }
    }

    const loadProgress = async () => {
      try {
        const res = await api.get('/progress')
        Object.assign(progress, res.data)
      } catch (e) {
        console.error('加载进度失败:', e)
      }
    }

    // ------------------ Scenegraph 检查与修复 ------------------
    const checkScenegraph = (scenegraphStr) => {
      let scenegraphData
      try {
        scenegraphData = JSON.parse(scenegraphStr || '[]')
      } catch (e) {
        return [`JSON解析错误: ${e.message}`]
      }
      if (!Array.isArray(scenegraphData)) return ['scenegraph必须是数组']

      const errors = []
      scenegraphData.forEach((tg, tIndex) => {
        if (!Array.isArray(tg.nodes)) errors.push(`时间组${tIndex}的nodes不是数组`)
        if (!Array.isArray(tg.edges)) errors.push(`时间组${tIndex}的edges不是数组`)
        const nodeIds = new Set((tg.nodes||[]).map(n => n.id))
        ;(tg.edges||[]).forEach((edge, eIndex) => {
          if (!Array.isArray(edge) || edge.length < 3) {
            errors.push(`时间组${tIndex}边${eIndex}不是长度为3数组`)
            return
          }
          const [src,, dst] = edge
          if (!nodeIds.has(src)) errors.push(`时间组${tIndex}边${eIndex}源节点 '${src}' 不存在`)
          if (!nodeIds.has(dst)) errors.push(`时间组${tIndex}边${eIndex}目标节点 '${dst}' 不存在`)
        })
      })
      return errors
    }

    const autoFixScenegraph = () => {
      let scenegraphData = []
      try {
        scenegraphData = JSON.parse(currentRow.scenegraph || '[]')
      } catch { scenegraphData = [] }
      scenegraphData.forEach(tg => {
        const nodeIds = new Set((tg.nodes||[]).map(n => n.id))
        tg.edges = (tg.edges||[]).map(edge => {
          const [src, rel, dst] = edge
          const newNodes = []
          if (!nodeIds.has(src)) {
            tg.nodes.push({id: src, attributes: []})
            nodeIds.add(src)
            newNodes.push(src)
          }
          if (!nodeIds.has(dst)) {
            tg.nodes.push({id: dst, attributes: []})
            nodeIds.add(dst)
            newNodes.push(dst)
          }
          return edge
        })
      })
      currentRow.scenegraph = JSON.stringify(scenegraphData)
      showSuccess('Scenegraph 自动修复完成')
      renderGraph()
      hasModifications.value = true
    }

    const saveRow = async () => {
      if (!hasModifications.value) return
      const errors = checkScenegraph(currentRow.scenegraph)
      if (errors.length > 0) return showError(`Scenegraph格式错误:\n${errors.join('\n')}`)

      saving.value = true
      try {
        await api.put(`/row/${currentRow.id}`, {
          input: currentRow.input,
          scenegraph: currentRow.scenegraph,
          is_reasonable: currentRow.is_reasonable,
          is_annotated: currentRow.is_annotated
        })
        hasModifications.value = false
        await loadProgress()
        showSuccess('保存成功')
        renderGraph()
      } catch (e) {
        showError(e.response?.data?.error || '保存失败')
      } finally {
        saving.value = false
      }
    }

    const previousRow = () => { if(currentIndex.value>0) loadRowByIndex(currentIndex.value-1) }
    const nextRow = () => { if(currentIndex.value<totalRows.value-1) loadRowByIndex(currentIndex.value+1) }

    const timeGroups = computed(() => {
      try { return JSON.parse(currentRow.scenegraph || '[]') } catch { return [] }
    })

    const renderGraph = () => {
      if (!graphContainer.value) return
      graphContainer.value.innerHTML = ''
      const main = document.createElement('div')
      main.style.cssText = `padding:20px;background:#f8f9fa;border-radius:8px;min-height:200px`
      const colors = ['#007bff','#28a745','#dc3545','#ffc107','#17a2b8','#6f42c1','#e83e8c','#fd7e14','#20c997','#6c757d']

      timeGroups.value.forEach((tg,tIndex) => {
        if(!tg.nodes) return
        const tgDiv = document.createElement('div')
        tgDiv.style.cssText = 'margin-bottom:30px;padding:15px;background:white;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)'
        const title = document.createElement('div')
        title.textContent = `时间组: ${tg.time||`T${tIndex+1}`}`
        title.style.cssText = `font-size:18px;font-weight:bold;color:#333;margin-bottom:15px;padding:10px;background:#e9ecef;border-radius:6px;text-align:center;border-left:4px solid ${colors[tIndex%colors.length]}`
        tgDiv.appendChild(title)

        const nodesContainer = document.createElement('div')
        nodesContainer.style.cssText = 'display:flex;flex-wrap:wrap;gap:10px;margin-bottom:15px'
        tg.nodes.forEach((node,nIndex)=>{
          const nodeEl = document.createElement('div')
          let content = `<div style="font-weight:bold;margin-bottom:5px">${node.id}</div>`
          if(node.attributes?.length>0) content += `<div style="font-size:12px;opacity:0.9">属性: ${node.attributes.join(', ')}</div>`
          nodeEl.innerHTML = content
          nodeEl.style.cssText = `background-color:${colors[nIndex%colors.length]};color:white;padding:12px 16px;border-radius:6px;text-align:center;min-width:120px;box-shadow:0 2px 4px rgba(0,0,0,0.1);cursor:pointer;transition:transform 0.2s`
          nodeEl.addEventListener('mouseenter',()=>nodeEl.style.transform='scale(1.05)')
          nodeEl.addEventListener('mouseleave',()=>nodeEl.style.transform='scale(1)')
          nodesContainer.appendChild(nodeEl)
        })
        tgDiv.appendChild(nodesContainer)

        if(tg.edges?.length>0){
          const edgesDiv = document.createElement('div')
          edgesDiv.style.cssText=`padding:15px;background:#f8f9fa;border-radius:6px;border-left:4px solid ${colors[tIndex%colors.length]}`
          const titleH = document.createElement('h4')
          titleH.textContent=`关系连接 (${tg.edges.length}条):`
          titleH.style.cssText='margin:0 0 10px 0;color:#333;font-size:14px'
          edgesDiv.appendChild(titleH)
          tg.edges.forEach((edge,eIndex)=>{
            if(Array.isArray(edge)&&edge.length>=3){
              const [src,rel,dst]=edge
              const eEl = document.createElement('div')
              eEl.style.cssText=`margin:5px 0;padding:8px 12px;background:white;border-radius:4px;font-size:14px;border-left:3px solid ${colors[eIndex%colors.length]}`
              eEl.innerHTML=`<strong>${src}</strong> <em style="color:#666">${rel}</em> <strong>${dst}</strong>`
              edgesDiv.appendChild(eEl)
            }
          })
          tgDiv.appendChild(edgesDiv)
        }
        main.appendChild(tgDiv)
      })
      graphContainer.value.appendChild(main)
    }

    return {
      filePath,fileLoaded,loading,saving,errorMessage,successMessage,
      currentRow,totalRows,currentIndex,hasModifications,progress,graphContainer,
      loadFile,saveRow,previousRow,nextRow,markAsModified,autoFixScenegraph
    }
  }
}
</script>

<style scoped>
.data-annotator {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.file-input {
  margin-bottom: 20px;
}

.file-input input {
  width: 70%;
  padding: 8px;
  margin-right: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.file-input button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.file-input button:hover {
  background: #0056b3;
}

.content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.text-section, .visualization-section {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
}

.text-section h3, .visualization-section h3 {
  margin-top: 0;
  color: #333;
}

.description {
  width: 100%;
  height: 150px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
}

.json-editor {
  height: 200px;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: auto;
}

.graph-container {
  height: 300px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #f8f9fa;
}

.time-groups {
  margin-bottom: 10px;
}

.time-group-btn {
  margin-right: 5px;
  padding: 5px 10px;
  border: 1px solid #007bff;
  background: white;
  color: #007bff;
  border-radius: 4px;
  cursor: pointer;
}

.time-group-btn.active {
  background: #007bff;
  color: white;
}

.controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.navigation {
  display: flex;
  gap: 10px;
}

.navigation button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.navigation button:hover {
  background: #f8f9fa;
}

.navigation button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.save-btn {
  padding: 10px 20px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.save-btn:hover {
  background: #218838;
}

.save-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.status {
  font-size: 14px;
  color: #666;
}

.error {
  color: #dc3545;
  background: #f8d7da;
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
}

.success {
  color: #155724;
  background: #d4edda;
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
}
</style>