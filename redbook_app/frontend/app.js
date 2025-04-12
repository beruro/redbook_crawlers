// 修改 API 基础 URL
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8008/api'
    : `${window.location.protocol}//${window.location.hostname}/api`;

// DOM元素
const urlsTextarea = document.getElementById('urls');
const processBtn = document.getElementById('processBtn');
const clearBtn = document.getElementById('clearBtn');
const fileUpload = document.getElementById('fileUpload');
const uploadBtn = document.getElementById('uploadBtn');
const statusCard = document.getElementById('statusCard');
const statusContainer = document.getElementById('statusContainer');
const downloadContainer = document.getElementById('downloadContainer');
const downloadBtn = document.getElementById('downloadBtn');

// 事件监听器
processBtn.addEventListener('click', processUrls);
clearBtn.addEventListener('click', clearUrls);
uploadBtn.addEventListener('click', uploadFile);
downloadBtn.addEventListener('click', downloadResult);

// 处理URL
async function processUrls() {
    const urls = urlsTextarea.value.trim();
    if (!urls) {
        alert('请输入至少一个URL');
        return;
    }
    
    try {
        processBtn.disabled = true;
        processBtn.textContent = '处理中...';
        
        const formData = new FormData();
        formData.append('urls', urls);
        
        const response = await fetch(`${API_BASE_URL}/process`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // 显示状态卡片
        statusCard.style.display = 'block';
        statusContainer.innerHTML = '<div class="status-item status-info">处理已开始，正在获取状态...</div>';
        
        // 开始轮询状态
        pollStatus();
    } catch (error) {
        console.error('处理URL时出错:', error);
        statusContainer.innerHTML = `<div class="status-item status-error">处理URL时出错: ${error.message}</div>`;
    } finally {
        processBtn.disabled = false;
        processBtn.textContent = '开始处理';
    }
}

// 清空URL
function clearUrls() {
    urlsTextarea.value = '';
}

// 上传文件
async function uploadFile() {
    const file = fileUpload.files[0];
    if (!file) {
        alert('请选择一个文件');
        return;
    }
    
    // 验证文件类型
    if (file.type !== 'text/plain' && !file.name.endsWith('.txt')) {
        alert('请上传 TXT 文本文件');
        return;
    }
    
    try {
        uploadBtn.disabled = true;
        uploadBtn.textContent = '上传中...';
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // 显示状态卡片
        statusCard.style.display = 'block';
        statusContainer.innerHTML = '<div class="status-item status-info">文件已上传，正在处理...</div>';
        
        // 开始轮询状态
        pollStatus();
    } catch (error) {
        console.error('上传文件时出错:', error);
        statusContainer.innerHTML = `<div class="status-item status-error">上传文件时出错: ${error.message}</div>`;
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '上传并处理';
    }
}

// 轮询状态
async function pollStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        const data = await response.json();
        
        // 更新状态显示
        updateStatusDisplay(data.status);
        
        // 检查是否有文件可下载
        if (data.file_path) {
            downloadContainer.style.display = 'block';
        } else {
            downloadContainer.style.display = 'none';
        }
        
        // 如果还在处理中，继续轮询
        const isProcessing = data.status.some(item => item.status === 'info' && item.message.includes('开始处理'));
        if (isProcessing) {
            setTimeout(pollStatus, 2000);
        }
    } catch (error) {
        console.error('获取状态时出错:', error);
        statusContainer.innerHTML += `<div class="status-item status-error">获取状态时出错: ${error.message}</div>`;
    }
}

// 更新状态显示
function updateStatusDisplay(statusList) {
    statusContainer.innerHTML = '';
    
    statusList.forEach(item => {
        const statusItem = document.createElement('div');
        statusItem.className = `status-item status-${item.status}`;
        statusItem.textContent = item.message;
        statusContainer.appendChild(statusItem);
    });
}

// 下载结果
async function downloadResult() {
    try {
        window.location.href = `${API_BASE_URL}/download`;
    } catch (error) {
        console.error('下载文件时出错:', error);
        alert(`下载文件时出错: ${error.message}`);
    }
} 