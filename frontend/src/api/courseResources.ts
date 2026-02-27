/**
 * 课程资源库管理API - 需求11专门实现
 * 支持词汇库、知识点库、教材库、考纲管理
 */

import { apiClient } from './client'

// =================== 类型定义 ===================

// 词汇库相关类型
export interface VocabularyItem {
  id: number
  word: string
  pronunciation: string
  partOfSpeech: string
  definitions: string[]
  chineseMeaning: string
  exampleSentences: string[]
  difficultyLevel: number // CEFR标准分级 1-6 (A1-C2)
  topicCategory: string
  frequencyRank: number
  synonyms: string[]
  antonyms: string[]
  collocations: string[]
  createdAt: string
  updatedAt: string
}

export interface VocabularyLibrary {
  id: number
  courseId: number
  name: string
  description: string
  itemCount: number
  permission: 'private' | 'class' | 'public'
  version: string
  createdAt: string
  updatedAt: string
  lastImportAt?: string
}

// 知识点库相关类型
export interface KnowledgePoint {
  id: number
  title: string
  description: string
  content: string
  category: string
  difficultyLevel: number
  prerequisites: number[] // 前置知识点ID
  relatedPoints: number[] // 相关知识点ID
  examples: string[]
  exercises: string[]
  tags: string[]
  createdAt: string
  updatedAt: string
}

export interface KnowledgeLibrary {
  id: number
  courseId: number
  name: string
  description: string
  itemCount: number
  permission: 'private' | 'class' | 'public'
  version: string
  createdAt: string
  updatedAt: string
}

// 教材库相关类型
export interface Material {
  id: number
  title: string
  isbn?: string
  publisher: string
  edition: string
  authors: string[]
  publicationYear: number
  description: string
  fileUrl?: string
  fileSize?: number
  fileFormat?: string
  chapters: MaterialChapter[]
  isCustom: boolean // 是否为自编教材
  createdAt: string
  updatedAt: string
}

export interface MaterialChapter {
  id: number
  title: string
  content: string
  pageStart: number
  pageEnd: number
  sections: MaterialSection[]
}

export interface MaterialSection {
  id: number
  title: string
  content: string
  exercises: string[]
}

export interface MaterialLibrary {
  id: number
  courseId: number
  materials: Material[]
  permission: 'private' | 'class' | 'public'
  createdAt: string
  updatedAt: string
}

// 考纲相关类型
export interface Syllabus {
  id: number
  courseId: number
  title: string
  version: string
  description: string
  objectives: string[]
  knowledgePoints: SyllabusKnowledgePoint[]
  assessmentCriteria: AssessmentCriterion[]
  timeAllocation: TimeAllocation[]
  references: string[]
  isActive: boolean
  parentSyllabusId?: number // 版本管理
  createdAt: string
  updatedAt: string
}

export interface SyllabusKnowledgePoint {
  id: number
  title: string
  description: string
  cognitiveLevel: string // 布鲁姆分类法
  weight: number // 权重
  requiredHours: number
  assessmentMethods: string[]
}

export interface AssessmentCriterion {
  id: number
  name: string
  description: string
  weight: number
  rubric: string[]
}

export interface TimeAllocation {
  id: number
  topic: string
  hours: number
  weeks: number[]
}

// 批量导入相关类型
export interface ImportResult {
  success: number
  failed: number
  total: number
  errors: ImportError[]
  warnings: ImportWarning[]
}

export interface ImportError {
  row: number
  field: string
  value: string
  message: string
}

export interface ImportWarning {
  row: number
  message: string
}

// 权限共享相关类型
export interface PermissionSetting {
  resourceType: 'vocabulary' | 'knowledge' | 'material' | 'syllabus'
  resourceId: number
  permission: 'private' | 'class' | 'public'
  sharedWith?: {
    classIds?: number[]
    teacherIds?: number[]
  }
}

// =================== API接口 ===================

export const courseResourcesApi = {
  // =================== 词汇库管理 ===================

  /**
   * 获取词汇库列表 - 需求11验收标准1
   */
  async getVocabularyLibraries(courseId: number): Promise<VocabularyLibrary[]> {
    const response = await apiClient.get(`/api/v1/resources/courses/${courseId}/vocabulary-libraries`)
    return response.data
  },

  /**
   * 创建词汇库
   */
  async createVocabularyLibrary(courseId: number, data: {
    name: string
    description: string
    permission: 'private' | 'class' | 'public'
  }): Promise<VocabularyLibrary> {
    const response = await apiClient.post(`/api/v1/resources/courses/${courseId}/vocabulary-libraries`, data)
    return response.data
  },

  /**
   * 获取词汇库中的词汇
   */
  async getVocabularyItems(libraryId: number, params?: {
    page?: number
    pageSize?: number
    search?: string
    category?: string
    difficultyLevel?: number
  }): Promise<{
    items: VocabularyItem[]
    total: number
    page: number
    pageSize: number
  }> {
    const response = await apiClient.get(`/api/v1/resources/vocabulary-libraries/${libraryId}/items`, { params })
    return response.data
  },

  /**
   * 批量导入词汇 - 需求11验收标准6
   */
  async importVocabulary(libraryId: number, file: File): Promise<ImportResult> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post(`/api/v1/resources/vocabulary-libraries/${libraryId}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * 下载词汇库模板
   */
  async downloadVocabularyTemplate(): Promise<Blob> {
    const response = await apiClient.get('/api/v1/resources/vocabulary-libraries/template', {
      responseType: 'blob',
    })
    return response.data
  },

  // =================== 知识点库管理 ===================

  /**
   * 获取知识点库列表 - 需求11验收标准2
   */
  async getKnowledgeLibraries(courseId: number): Promise<KnowledgeLibrary[]> {
    const response = await apiClient.get(`/api/v1/resources/courses/${courseId}/knowledge-libraries`)
    return response.data
  },

  /**
   * 创建知识点库
   */
  async createKnowledgeLibrary(courseId: number, data: {
    name: string
    description: string
    permission: 'private' | 'class' | 'public'
  }): Promise<KnowledgeLibrary> {
    const response = await apiClient.post(`/api/v1/resources/courses/${courseId}/knowledge-libraries`, data)
    return response.data
  },

  /**
   * 获取知识点
   */
  async getKnowledgePoints(libraryId: number, params?: {
    page?: number
    pageSize?: number
    search?: string
    category?: string
    difficultyLevel?: number
  }): Promise<{
    items: KnowledgePoint[]
    total: number
    page: number
    pageSize: number
  }> {
    const response = await apiClient.get(`/api/v1/resources/knowledge-libraries/${libraryId}/points`, { params })
    return response.data
  },

  /**
   * 批量导入知识点 - 需求11验收标准6
   */
  async importKnowledgePoints(libraryId: number, file: File): Promise<ImportResult> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post(`/api/v1/resources/knowledge-libraries/${libraryId}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // =================== 教材库管理 ===================

  /**
   * 获取教材库 - 需求11验收标准3
   */
  async getMaterialLibrary(courseId: number): Promise<MaterialLibrary> {
    const response = await apiClient.get(`/api/v1/resources/courses/${courseId}/material-library`)
    return response.data
  },

  /**
   * 添加教材
   */
  async addMaterial(courseId: number, data: {
    title: string
    isbn?: string
    publisher: string
    edition: string
    authors: string[]
    publicationYear: number
    description: string
    isCustom: boolean
  }): Promise<Material> {
    const response = await apiClient.post(`/api/v1/resources/courses/${courseId}/materials`, data)
    return response.data
  },

  /**
   * 上传自编教材
   */
  async uploadCustomMaterial(courseId: number, file: File, metadata: {
    title: string
    description: string
    authors: string[]
  }): Promise<Material> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('metadata', JSON.stringify(metadata))
    
    const response = await apiClient.post(`/api/v1/resources/courses/${courseId}/materials/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // =================== 考纲管理 ===================

  /**
   * 获取考纲 - 需求11验收标准4
   */
  async getSyllabus(courseId: number): Promise<Syllabus | null> {
    const response = await apiClient.get(`/api/v1/resources/courses/${courseId}/syllabus`)
    return response.data
  },

  /**
   * 创建考纲
   */
  async createSyllabus(courseId: number, data: {
    title: string
    description: string
    objectives: string[]
    knowledgePoints: Omit<SyllabusKnowledgePoint, 'id'>[]
  }): Promise<Syllabus> {
    const response = await apiClient.post(`/api/v1/resources/courses/${courseId}/syllabus`, data)
    return response.data
  },

  /**
   * 更新考纲版本
   */
  async updateSyllabus(syllabusId: number, data: Partial<Syllabus>): Promise<Syllabus> {
    const response = await apiClient.put(`/api/v1/resources/syllabus/${syllabusId}`, data)
    return response.data
  },

  /**
   * 获取考纲版本历史
   */
  async getSyllabusVersions(courseId: number): Promise<Syllabus[]> {
    const response = await apiClient.get(`/api/v1/resources/courses/${courseId}/syllabus/versions`)
    return response.data
  },

  // =================== 权限管理 ===================

  /**
   * 设置资源权限 - 需求11验收标准5
   */
  async setResourcePermission(setting: PermissionSetting): Promise<{ success: boolean }> {
    const response = await apiClient.post('/api/v1/resources/permissions', setting)
    return response.data
  },

  /**
   * 获取共享资源
   */
  async getSharedResources(resourceType: 'vocabulary' | 'knowledge' | 'material' | 'syllabus'): Promise<any[]> {
    const response = await apiClient.get(`/api/v1/resources/shared/${resourceType}`)
    return response.data
  },

  // =================== 版本控制 ===================

  /**
   * 获取资源版本历史 - 需求11验收标准6
   */
  async getResourceVersions(resourceType: string, resourceId: number): Promise<any[]> {
    const response = await apiClient.get(`/api/v1/resources/${resourceType}/${resourceId}/versions`)
    return response.data
  },

  /**
   * 回滚到指定版本
   */
  async rollbackToVersion(resourceType: string, resourceId: number, versionId: number): Promise<{ success: boolean }> {
    const response = await apiClient.post(`/api/v1/resources/${resourceType}/${resourceId}/rollback`, {
      versionId,
    })
    return response.data
  },
}
