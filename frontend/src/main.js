import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia() // 2. 建立 Pinia 實例

app.use(pinia) // 3. 註冊 Pinia (必須在 mount 之前！)
app.use(router)

app.mount('#app')
