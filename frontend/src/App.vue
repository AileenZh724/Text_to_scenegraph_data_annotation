<template>
  <div id="app">
    <!-- 文件路径输入区域 -->
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
          {{ errorMessage }}
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

      <!-- 标注控制区域 -->
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
        
        <!-- 导航和保存控制 -->
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
            @click="showEvaluationModal = true"
            class="btn btn-info"
            :disabled="!fileLoaded"
          >
            评估
          </button>
        </div>
      </div>
    </div>

    <!-- 评估模态框 -->
    <div v-if="showEvaluationModal" class="modal-overlay" @click="closeEvaluationModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>场景图评估</h3>
          <button @click="closeEvaluationModal" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="evaluation-tabs">
            <button 
              @click="evaluationTab = 'current'"
              :class="['tab-btn', { active: evaluationTab === 'current' }]"
            >
              当前数据评估
            </button>
            <button 
              @click="evaluationTab = 'file'"
              :class="['tab-btn', { active: evaluationTab === 'file' }]"
            >
              文件比较评估
            </button>
          </div>
          
          <!-- 当前数据评估 -->
          <div v-if="evaluationTab === 'current'" class="evaluation-content">
            <div class="form-group">
              <label>K值设置（用于Recall@K）:</label>
              <input 
                v-model="evaluationSettings.kValues" 
                type="text" 
                placeholder="例如: 1,5,10,20,50,100"
                class="form-input"
              />
              <small>用逗号分隔多个K值</small>
            </div>
            
            <div class="form-group">
              <label>已见谓词（用于Zero-shot评估，可选）:</label>
              <textarea 
                v-model="evaluationSettings.seenPredicatesText" 
                placeholder='输入已见谓词列表，每行一个，例如：&#10;on&#10;in&#10;next to'
                class="form-textarea"
                rows="4"
              ></textarea>
            </div>
            
            <button 
              @click="runCurrentDataEvaluation" 
              class="btn btn-primary"
              :disabled="evaluating"
            >
              {{ evaluating ? '评估中...' : '开始评估' }}
            </button>
          </div>
          
          <!-- 文件比较评估 -->
          <div v-if="evaluationTab === 'file'" class="evaluation-content">
            <div class="form-group">
              <label>预测数据文件路径:</label>
              <input 
                v-model="evaluationSettings.predFile" 
                type="text" 
                placeholder="预测结果JSON文件路径"
                class="form-input"
              />
            </div>
            
            <div class="form-group">
              <label>真实数据文件路径:</label>
              <input 
                v-model="evaluationSettings.gtFile" 
                type="text" 
                placeholder="真实标签JSON文件路径"
                class="form-input"
              />
            </div>
            
            <div class="form-group">
              <label>对齐方式:</label>
              <select v-model="evaluationSettings.alignBy" class="form-select">
                <option value="index">按索引对齐</option>
                <option value="id">按ID对齐</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>长度不匹配处理:</label>
              <select v-model="evaluationSettings.alignMode" class="form-select">
                <option value="error">报错</option>
                <option value="min">取最小长度</option>
                <option value="gt">以真实数据为准</option>
                <option value="pred">以预测数据为准</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>K值设置:</label>
              <input 
                v-model="evaluationSettings.kValues" 
                type="text" 
                placeholder="例如: 1,5,10,20,50,100"
                class="form-input"
              />
            </div>
            
            <div class="form-group">
              <label>已见谓词（可选）:</label>
              <textarea 
                v-model="evaluationSettings.seenPredicatesText" 
                placeholder='输入已见谓词列表，每行一个'
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>
            
            <button 
              @click="runFileEvaluation" 
              class="btn btn-primary"
              :disabled="evaluating"
            >
              {{ evaluating ? '评估中...' : '开始评估' }}
            </button>
          </div>
          
          <!-- 评估结果 -->
          <div v-if="evaluationResults" class="evaluation-results">
            <h4>评估结果</h4>
            <div class="results-grid">
              <div v-for="(value, key) in filteredResults" :key="key" class="result-item">
                <span class="result-label">{{ formatMetricName(key) }}:</span>
                <span class="result-value">{{ formatValue(value) }}</span>
              </div>
            </div>
            
            <div v-if="evaluationResults.statistics" class="statistics">
              <h5>统计信息</h5>
              <div class="stats-grid">
                <div v-for="(value, key) in evaluationResults.statistics" :key="key" class="stat-item">
                  <span class="stat-label">{{ formatStatName(key) }}:</span>
                  <span class="stat-value">{{ formatValue(value) }}</span>
                </div>
              </div>
            </div>
            
            <div class="export-section">
              <h5>导出结果</h5>
              <div class="export-controls">
                <select v-model="exportFormat" class="form-select">
                  <option value="json">JSON</option>
                  <option value="csv">CSV</option>
                  <option value="txt">TXT</option>
                </select>
                <input 
                  v-model="exportFilename" 
                  type="text" 
                  placeholder="输出文件名（不含扩展名）"
                  class="form-input"
                />
                <button @click="exportResults" class="btn btn-secondary">导出</button>
              </div>
            </div>
          </div>
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
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'

export default {
  name: 'App',
  setup() {
    // 响应式数据
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
      scenegraph: '',
      is_reasonable: false,
      is_annotated: false
    })
    
    const currentIndex = ref(0)
    const totalRows = ref(0)
    const activeTimeIndex = ref(0)
    
    const progress = reactive({
      total: 0,
      annotated: 0,
      reasonable: 0
    })
    
    // DOM引用
    const graphContainer = ref(null)
    
    // 评估相关的响应式数据
    const showEvaluationModal = ref(false)
    const evaluationTab = ref('current')
    const evaluating = ref(false)
    const evaluationResults = ref(null)
    const exportFormat = ref('json')
    const exportFilename = ref('evaluation_results')
    
    const evaluationSettings = reactive({
      kValues: '1,5,10,20,50,100',
      seenPredicatesText: '',
      predFile: '',
      gtFile: '',
      alignBy: 'index',
      alignMode: 'error'
    })
    
    // 计算属性
    const timeGroups = computed(() => {
      try {
        const scenegraphData = JSON.parse(currentRow.scenegraph || '[]')
        return Array.isArray(scenegraphData) ? scenegraphData : []
      } catch {
        return []
      }
    })
    
    const filteredResults = computed(() => {
      if (!evaluationResults.value) return {}
      
      // 过滤掉statistics字段，只显示指标结果
      const filtered = {}
      for (const [key, value] of Object.entries(evaluationResults.value)) {
        if (key !== 'statistics' && typeof value === 'number') {
          filtered[key] = value
        }
      }
      return filtered
    })
    
    // API配置
    const api = axios.create({
      baseURL: '/api',
      timeout: 10000
    })
    
    // 方法
    const showError = (message) => {
      errorMessage.value = message
      successMessage.value = ''
      setTimeout(() => {
        errorMessage.value = ''
      }, 5000)
    }
    
    const showSuccess = (message) => {
      successMessage.value = message
      errorMessage.value = ''
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)
    }
    
    const markAsModified = () => {
      hasModifications.value = true
    }
    
    const loadFile = async () => {
      if (!filePath.value.trim()) {
        showError('请输入文件路径')
        return
      }
      
      loading.value = true
      errorMessage.value = ''
      
      try {
        const response = await api.post('/open', { path: filePath.value })
        
        if (response.data.success) {
          fileLoaded.value = true
          totalRows.value = response.data.total_rows
          localStorage.setItem('lastFilePath', filePath.value)
          
          // 加载第一行数据
          await loadRowByIndex(0)
          await loadProgress()
          

          
          showSuccess(`成功加载文件，共 ${totalRows.value} 行数据`)
        }
      } catch (error) {
        showError(error.response?.data?.error || '加载文件失败')
      } finally {
        loading.value = false
      }
    }
    
    const loadRowByIndex = async (index) => {
      try {
        const response = await api.get(`/row?index=${index}`)
        const rowData = response.data
        
        Object.assign(currentRow, rowData)
        currentIndex.value = index
        hasModifications.value = false
        activeTimeIndex.value = 0
        
        // 更新图形
        await nextTick()
        renderGraph()
      } catch (error) {
        showError(error.response?.data?.error || '加载行数据失败')
      }
    }
    
    const loadProgress = async () => {
      try {
        const response = await api.get('/progress')
        Object.assign(progress, response.data)
      } catch (error) {
        console.error('加载进度失败:', error)
      }
    }
    
    const saveRow = async () => {
      if (!hasModifications.value) return
      
      // 验证JSON格式
      try {
        const scenegraphData = JSON.parse(currentRow.scenegraph)
        validateScenegraph(scenegraphData)
      } catch (error) {
        showError(`Scenegraph格式错误: ${error.message}`)
        return
      }
      
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
        
        // 重新渲染图形
        renderGraph()
      } catch (error) {
        showError(error.response?.data?.error || '保存失败')
      } finally {
        saving.value = false
      }
    }
    
    const validateScenegraph = (data) => {
      if (!Array.isArray(data)) {
        throw new Error('scenegraph必须是数组')
      }
      
      data.forEach((timeGroup, i) => {
        if (!timeGroup.time) {
          throw new Error(`时间组${i}缺少time字段`)
        }
        if (!Array.isArray(timeGroup.nodes)) {
          throw new Error(`时间组${i}的nodes必须是数组`)
        }
        if (!Array.isArray(timeGroup.edges)) {
          throw new Error(`时间组${i}的edges必须是数组`)
        }
        
        const nodeIds = new Set()
        timeGroup.nodes.forEach((node, j) => {
          if (!node.id) {
            throw new Error(`时间组${i}节点${j}缺少id字段`)
          }
          if (nodeIds.has(node.id)) {
            throw new Error(`时间组${i}中节点ID '${node.id}' 重复`)
          }
          nodeIds.add(node.id)
        })
        
        timeGroup.edges.forEach((edge, j) => {
          if (!Array.isArray(edge) || edge.length !== 3) {
            throw new Error(`时间组${i}边${j}必须是包含3个元素的数组`)
          }
          const [src, rel, dst] = edge
          if (!nodeIds.has(src)) {
            throw new Error(`时间组${i}边${j}的源节点'${src}'不存在`)
          }
          if (!nodeIds.has(dst)) {
            throw new Error(`时间组${i}边${j}的目标节点'${dst}'不存在`)
          }
        })
      })
    }
    
    const previousRow = () => {
      if (currentIndex.value > 0) {
        loadRowByIndex(currentIndex.value - 1)
      }
    }
    
    const nextRow = () => {
      if (currentIndex.value < totalRows.value - 1) {
        loadRowByIndex(currentIndex.value + 1)
      }
    }
    

    
    const renderGraph = () => {
      if (!graphContainer.value || timeGroups.value.length === 0) return
      
      // 清除现有内容
      graphContainer.value.innerHTML = ''
      
      // 创建主容器
       const mainContainer = document.createElement('div')
       mainContainer.style.cssText = `
         padding: 20px;
         background: #f8f9fa;
         border-radius: 8px;
         min-height: 200px;
         user-select: none;
         -webkit-user-drag: none;
         -moz-user-select: none;
         -ms-user-select: none;
       `
      
      // 定义颜色数组
      const colors = [
        '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
        '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6c757d'
      ]
      
      // 遍历所有时间组
      timeGroups.value.forEach((timeGroup, timeIndex) => {
        if (!timeGroup.nodes) return
        
        // 创建时间组容器
        const timeGroupContainer = document.createElement('div')
        timeGroupContainer.style.cssText = `
          margin-bottom: 30px;
          padding: 15px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        `
        
        // 添加时间组标题
        const timeTitle = document.createElement('div')
        timeTitle.style.cssText = `
          font-size: 18px;
          font-weight: bold;
          color: #333;
          margin-bottom: 15px;
          padding: 10px;
          background: #e9ecef;
          border-radius: 6px;
          text-align: center;
          border-left: 4px solid ${colors[timeIndex % colors.length]};
        `
        timeTitle.textContent = `时间组: ${timeGroup.time || `T${timeIndex + 1}`}`
        timeGroupContainer.appendChild(timeTitle)
        
        // 添加节点容器
        const nodesContainer = document.createElement('div')
        nodesContainer.style.cssText = `
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin-bottom: 15px;
        `
        
        // 添加节点方块
        timeGroup.nodes.forEach((node, index) => {
          const nodeElement = document.createElement('div')
          const color = colors[index % colors.length]
          
          // 创建节点内容，包含属性
          let nodeContent = `<div style="font-weight: bold; margin-bottom: 5px;">${node.id}</div>`
          if (node.attributes && node.attributes.length > 0) {
            nodeContent += `<div style="font-size: 12px; opacity: 0.9;">属性: ${node.attributes.join(', ')}</div>`
          }
          
          nodeElement.innerHTML = nodeContent
          nodeElement.style.cssText = `
            background-color: ${color};
            color: white;
            padding: 12px 16px;
            border-radius: 6px;
            text-align: center;
            min-width: 120px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s;
          `
          
          // 添加悬停效果
          nodeElement.addEventListener('mouseenter', () => {
            nodeElement.style.transform = 'scale(1.05)'
          })
          nodeElement.addEventListener('mouseleave', () => {
            nodeElement.style.transform = 'scale(1)'
          })
          
          nodesContainer.appendChild(nodeElement)
        })
        
        timeGroupContainer.appendChild(nodesContainer)
        
        // 添加边信息
        if (timeGroup.edges && timeGroup.edges.length > 0) {
          const edgesInfo = document.createElement('div')
          edgesInfo.style.cssText = `
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid ${colors[timeIndex % colors.length]};
          `
          
          const edgesTitle = document.createElement('h4')
          edgesTitle.textContent = `关系连接 (${timeGroup.edges.length}条):`
          edgesTitle.style.cssText = 'margin: 0 0 10px 0; color: #333; font-size: 14px;'
          edgesInfo.appendChild(edgesTitle)
          
          timeGroup.edges.forEach((edge, index) => {
            if (Array.isArray(edge) && edge.length >= 3) {
              const [src, relation, dst] = edge
              const edgeElement = document.createElement('div')
              edgeElement.style.cssText = `
                margin: 5px 0;
                padding: 8px 12px;
                background: white;
                border-radius: 4px;
                font-size: 14px;
                border-left: 3px solid ${colors[index % colors.length]};
              `
              edgeElement.innerHTML = `<strong>${src}</strong> <em style="color: #666;">${relation}</em> <strong>${dst}</strong>`
              edgesInfo.appendChild(edgeElement)
            }
          })
          
          timeGroupContainer.appendChild(edgesInfo)
        } else {
          // 显示无边信息
          const noEdgesInfo = document.createElement('div')
          noEdgesInfo.style.cssText = `
            padding: 15px;
            background: #fff3cd;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
            text-align: center;
            color: #856404;
            font-style: italic;
          `
          noEdgesInfo.textContent = '该时间组没有关系连接'
          timeGroupContainer.appendChild(noEdgesInfo)
        }
        
        mainContainer.appendChild(timeGroupContainer)
      })
      
      graphContainer.value.appendChild(mainContainer)
    }
    
    const switchTimeGroup = (index) => {
      activeTimeIndex.value = index
      renderGraph()
    }
    
    // 评估相关方法
    const closeEvaluationModal = () => {
      showEvaluationModal.value = false
      evaluationResults.value = null
    }
    
    const parseKValues = (kValuesStr) => {
      try {
        return kValuesStr.split(',').map(k => parseInt(k.trim())).filter(k => !isNaN(k))
      } catch {
        return [1, 5, 10, 20, 50, 100]
      }
    }
    
    const parseSeenPredicates = (seenPredicatesText) => {
      if (!seenPredicatesText.trim()) return null
      return seenPredicatesText.split('\n').map(line => line.trim()).filter(line => line)
    }
    
    const runCurrentDataEvaluation = async () => {
      evaluating.value = true
      try {
        const kValues = parseKValues(evaluationSettings.kValues)
        const seenPredicates = parseSeenPredicates(evaluationSettings.seenPredicatesText)
        
        const response = await api.post('/evaluate', {
          type: 'current',
          k_values: kValues,
          seen_predicates: seenPredicates
        })
        
        evaluationResults.value = response.data.results
        showSuccess('当前数据评估完成')
      } catch (error) {
        showError(error.response?.data?.error || '评估失败: ' + error.message)
      } finally {
        evaluating.value = false
      }
    }
    
    const runFileEvaluation = async () => {
      if (!evaluationSettings.predFile || !evaluationSettings.gtFile) {
        showError('请输入预测文件和真实数据文件路径')
        return
      }
      
      evaluating.value = true
      try {
        const kValues = parseKValues(evaluationSettings.kValues)
        const seenPredicates = parseSeenPredicates(evaluationSettings.seenPredicatesText)
        
        const response = await api.post('/evaluate', {
          type: 'file',
          pred_file: evaluationSettings.predFile,
          gt_file: evaluationSettings.gtFile,
          k_values: kValues,
          seen_predicates: seenPredicates,
          align_by: evaluationSettings.alignBy,
          align_mode: evaluationSettings.alignMode
        })
        
        evaluationResults.value = response.data.results
        showSuccess('文件评估完成')
      } catch (error) {
        showError(error.response?.data?.error || '评估失败: ' + error.message)
      } finally {
        evaluating.value = false
      }
    }
    
    const exportResults = async () => {
      if (!evaluationResults.value) {
        showError('没有可导出的评估结果')
        return
      }
      
      try {
        const response = await api.post('/evaluate/export', {
          results: evaluationResults.value,
          format: exportFormat.value,
          output_file: exportFilename.value
        })
        
        showSuccess(response.data.message)
      } catch (error) {
        showError(error.response?.data?.error || '导出失败: ' + error.message)
      }
    }
    
    const formatMetricName = (key) => {
      const names = {
        'precision': '精确率',
        'recall': '召回率',
        'f1': 'F1分数'
      }
      
      if (names[key]) return names[key]
      
      if (key.startsWith('recall@')) {
        const k = key.substring(7)
        return `Recall@${k}`
      }
      
      if (key.startsWith('mean_recall@')) {
        const k = key.substring(12)
        return `Mean Recall@${k}`
      }
      
      if (key.startsWith('zero_shot_recall@')) {
        const k = key.substring(17)
        return `Zero-shot Recall@${k}`
      }
      
      return key
    }
    
    const formatStatName = (key) => {
      const names = {
        'total_items': '总项目数',
        'total_pred_triples': '预测三元组总数',
        'total_gt_triples': '真实三元组总数',
        'avg_pred_triples_per_item': '平均预测三元组数/项目',
        'avg_gt_triples_per_item': '平均真实三元组数/项目'
      }
      return names[key] || key
    }
    
    const formatValue = (value) => {
      if (typeof value === 'number') {
        if (value < 1 && value > 0) {
          return value.toFixed(4)
        }
        return value.toString()
      }
      return value
    }

    
    return {
      filePath,
      fileLoaded,
      loading,
      saving,
      errorMessage,
      successMessage,
      currentRow,
      totalRows,
      currentIndex,
      hasModifications,
      progress,
      graphContainer,
      timeGroups,
      activeTimeIndex,
      loadFile,
      saveRow,
      previousRow,
      nextRow,
      switchTimeGroup,
      markAsModified,
      // 评估相关
      showEvaluationModal,
      evaluationTab,
      evaluating,
      evaluationResults,
      evaluationSettings,
      exportFormat,
      exportFilename,
      filteredResults,
      closeEvaluationModal,
      runCurrentDataEvaluation,
      runFileEvaluation,
      exportResults,
      formatMetricName,
      formatStatName,
      formatValue
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

/* 评估模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background-color: #f0f0f0;
  color: #666;
}

.modal-body {
  padding: 20px;
}

.evaluation-tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.tab-btn {
  background: none;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #007bff;
  border-bottom-color: #007bff;
  font-weight: 600;
}

.tab-btn:hover {
  color: #007bff;
  background-color: #f8f9fa;
}

.evaluation-content {
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #333;
}

.form-input, .form-textarea, .form-select {
  width: 100%;
  padding: 10px;
  border: 2px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus, .form-textarea:focus, .form-select:focus {
  outline: none;
  border-color: #007bff;
}

.form-group small {
  display: block;
  margin-top: 5px;
  color: #666;
  font-size: 12px;
}

.evaluation-results {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.evaluation-results h4 {
  margin: 0 0 20px 0;
  color: #333;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 4px solid #007bff;
}

.result-label {
  font-weight: 600;
  color: #333;
}

.result-value {
  font-family: 'Courier New', monospace;
  font-weight: bold;
  color: #007bff;
}

.statistics {
  margin-bottom: 30px;
}

.statistics h5 {
  margin: 0 0 15px 0;
  color: #666;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 14px;
}

.stat-label {
  color: #666;
}

.stat-value {
  font-family: 'Courier New', monospace;
  font-weight: bold;
  color: #333;
}

.export-section {
  border-top: 1px solid #e0e0e0;
  padding-top: 20px;
}

.export-section h5 {
  margin: 0 0 15px 0;
  color: #666;
}

.export-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.export-controls .form-select,
.export-controls .form-input {
  flex: 1;
  min-width: 150px;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
  border: none;
}

.btn-info:hover {
  background-color: #138496;
}

.btn-info:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
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