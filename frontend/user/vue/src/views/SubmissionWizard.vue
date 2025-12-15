<template>
  <div class="wizard">
    <h1>Express Diagnostics</h1>

    <div class="steps">
      <span :class="{ active: step === 1, completed: step > 1 }">1. Upload</span>
      <span :class="{ active: step === 2, completed: step > 2 }">2. Contact</span>
      <span :class="{ active: step === 3 }">3. Confirm</span>
    </div>

    <!-- Step 1: Upload Images -->
    <div v-if="step === 1" class="step-content">
      <h2>Upload Your Images</h2>
      <p>Please upload images for diagnostic analysis.</p>

      <input
        type="file"
        multiple
        accept="image/jpeg,image/png,image/webp"
        @change="handleFileUpload"
        class="file-input"
      />

      <div v-if="images.length" class="preview">
        <div v-for="(img, i) in images" :key="i" class="preview-item">
          <img :src="img.preview" alt="Preview" />
          <button @click="removeImage(i)" class="remove-btn">X</button>
        </div>
      </div>

      <textarea
        v-model="comments"
        placeholder="Add any comments about your images (optional)..."
        class="comments"
      ></textarea>

      <button @click="nextStep" :disabled="!images.length" class="btn-primary">
        Next
      </button>
    </div>

    <!-- Step 2: Contact & Consent -->
    <div v-if="step === 2" class="step-content">
      <h2>Contact Information</h2>

      <div class="form-group">
        <label for="email">Email Address</label>
        <input
          id="email"
          v-model="email"
          type="email"
          placeholder="your@email.com"
          class="input"
        />
      </div>

      <div class="consent">
        <h3>Data Processing Agreement</h3>
        <p class="consent-text">
          By submitting this form, you agree that your uploaded images and personal data
          will be processed for diagnostic purposes. Your data will be handled in accordance
          with applicable data protection regulations.
        </p>
        <label class="checkbox-label">
          <input type="checkbox" v-model="consent" />
          I agree to the data processing terms
        </label>
      </div>

      <div class="buttons">
        <button @click="prevStep" class="btn-secondary">Back</button>
        <button @click="submitData" :disabled="!canSubmit || loading" class="btn-primary">
          {{ loading ? 'Submitting...' : 'Submit' }}
        </button>
      </div>
    </div>

    <!-- Step 3: Confirmation -->
    <div v-if="step === 3" class="step-content">
      <div class="success-icon">&#10003;</div>
      <h2>Submission Received</h2>
      <p>Your data has been submitted successfully.</p>
      <p>You will receive results via email at <strong>{{ email }}</strong></p>

      <div v-if="statusMessage" class="status-update">
        <p><strong>Status:</strong> {{ statusMessage }}</p>
      </div>

      <button @click="startNew" class="btn-secondary">Submit Another</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useSubmissionStore } from '@/stores/submission'
import { io } from 'socket.io-client'

const store = useSubmissionStore()

const step = ref(1)
const images = ref([])
const comments = ref('')
const email = ref('')
const consent = ref(false)
const statusMessage = ref('')
const loading = ref(false)
let socket = null

const canSubmit = computed(() => email.value && consent.value && !loading.value)

function handleFileUpload(event) {
  const files = Array.from(event.target.files)
  files.forEach(file => {
    const reader = new FileReader()
    reader.onload = (e) => {
      images.value.push({
        file,
        preview: e.target.result,
        type: file.type,
        size: file.size
      })
    }
    reader.readAsDataURL(file)
  })
}

function removeImage(index) {
  images.value.splice(index, 1)
}

function nextStep() {
  step.value++
}

function prevStep() {
  step.value--
}

async function submitData() {
  loading.value = true

  try {
    await store.submit({
      images: images.value.map(img => ({
        data: img.preview,
        type: img.type,
        size: img.size
      })),
      comments: comments.value,
      email: email.value,
      consent: consent.value
    })

    step.value = 3
    connectSocket()

  } catch (error) {
    alert('Submission failed: ' + (error.response?.data?.errors?.join(', ') || error.message))
  } finally {
    loading.value = false
  }
}

function connectSocket() {
  socket = io()

  socket.emit('subscribe', { email: email.value })

  socket.on('status_update', (data) => {
    statusMessage.value = data.message
  })

  socket.on('result_ready', () => {
    statusMessage.value = 'Your results are ready! Check your email.'
  })
}

function startNew() {
  step.value = 1
  images.value = []
  comments.value = ''
  email.value = ''
  consent.value = false
  statusMessage.value = ''
  store.reset()

  if (socket) {
    socket.disconnect()
    socket = null
  }
}

onUnmounted(() => {
  if (socket) {
    socket.disconnect()
  }
})
</script>

<style scoped>
.wizard {
  max-width: 600px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
}

.steps span {
  padding: 10px 20px;
  background: #eee;
  border-radius: 4px;
  font-size: 14px;
}

.steps span.active {
  background: #007bff;
  color: white;
}

.steps span.completed {
  background: #28a745;
  color: white;
}

.step-content {
  padding: 30px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
}

.step-content h2 {
  margin-bottom: 20px;
}

.file-input {
  display: block;
  margin: 20px 0;
}

.preview {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 20px 0;
}

.preview-item {
  position: relative;
}

.preview-item img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 4px;
}

.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #dc3545;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 12px;
}

.comments, .input {
  width: 100%;
  padding: 12px;
  margin: 10px 0;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.comments {
  min-height: 100px;
  resize: vertical;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.consent {
  margin: 20px 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
}

.consent h3 {
  margin-bottom: 10px;
}

.consent-text {
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-primary, .btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.success-icon {
  width: 60px;
  height: 60px;
  background: #28a745;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  margin: 0 auto 20px;
}

.status-update {
  margin-top: 20px;
  padding: 15px;
  background: #e7f3ff;
  border-radius: 4px;
  border-left: 4px solid #007bff;
}
</style>
