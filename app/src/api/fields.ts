import { ajax } from './ajax'

export interface FieldConfig {
  options?: { label: string; value: string }[]
}

export interface FormField {
  field_id: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'radio' | 'checkbox' | 'date' | 'time' | 'datetime' | 'file'
  required: boolean
  placeholder: string
  sort_order: number
  config: FieldConfig
}

export const getFields = () => ajax<FormField[]>('/admin/settings/fields', { method: 'GET' })

export const createField = (data: Omit<FormField, 'field_id' | 'sort_order'>) => 
  ajax('/admin/settings/fields', { method: 'POST', body: data })

export const updateField = (field_id: string, data: Partial<FormField>) => 
  ajax(`/admin/settings/fields/${field_id}`, { method: 'PATCH', body: data })

export const deleteField = (field_id: string) => 
  ajax(`/admin/settings/fields/${field_id}`, { method: 'DELETE' })

export const reorderFields = (orders: { field_id: string; sort_order: number }[]) => 
  ajax('/admin/settings/fields/reorder', { method: 'POST', body: { fields: orders } })
