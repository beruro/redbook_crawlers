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
const excelUpload = document.getElementById('excelUpload');
const columnInput = document.getElementById('columnInput');
const uploadExcelBtn = document.getElementById('uploadExcelBtn');

// Cookie相关DOM元素
const cookieInput = document.getElementById('cookieInput');
const updateCookieBtn = document.getElementById('updateCookieBtn');
const getCurrentCookieBtn = document.getElementById('getCurrentCookieBtn');
const validateCookieBtn = document.getElementById('validateCookieBtn');
const cookieStatus = document.getElementById('cookieStatus');
const cookieInfo = document.getElementById('cookieInfo');

// 事件监听器
processBtn.addEventListener('click', processUrls);
clearBtn.addEventListener('click', clearUrls);
uploadBtn.addEventListener('click', uploadFile);
downloadBtn.addEventListener('click', downloadResult);
uploadExcelBtn.addEventListener('click', uploadExcelFile);

// Cookie相关事件监听器
updateCookieBtn.addEventListener('click', updateCookie);
getCurrentCookieBtn.addEventListener('click', getCurrentCookie);
validateCookieBtn.addEventListener('click', validateCookie);

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
        
        // 检查响应状态
        if (!response.ok) {
            console.error(`HTTP错误: ${response.status}`);
            // 即使HTTP错误，也等待一段时间后显示下载按钮
            setTimeout(() => {
                downloadContainer.style.display = 'block';
                statusContainer.innerHTML += `<div class="status-item status-info">⚠️ 状态查询异常，但可能处理已完成，请尝试下载</div>`;
            }, 5000);
            return;
        }
        
        // 先获取响应文本，然后尝试解析JSON
        const responseText = await response.text();
        let data;
        
        try {
            data = JSON.parse(responseText);
        } catch (jsonError) {
            console.warn('JSON解析失败，可能是处理完成:', jsonError);
            console.log('响应内容:', responseText);
            
            // JSON解析失败通常意味着处理已完成，显示下载按钮
            downloadContainer.style.display = 'block';
            statusContainer.innerHTML += `<div class="status-item status-info">✅ 处理完成信号检测到，请尝试下载结果</div>`;
            return; // 停止轮询
        }
        
        // 更新状态显示
        updateStatusDisplay(data.status || []);
        
        // 检查是否有文件可下载
        if (data.file_path) {
            downloadContainer.style.display = 'block';
        } else {
            // 即使没有file_path，也检查状态中是否有成功保存的消息
            const hasSuccessfulSave = data.status && data.status.some(item => 
                item.status === 'success' && item.message && item.message.includes('数据已保存')
            );
            
            if (hasSuccessfulSave) {
                downloadContainer.style.display = 'block';
                console.log('检测到数据已保存，显示下载按钮');
            }
        }
        
        // 检查是否还在处理中
        const isProcessing = data.status && data.status.some(item => 
            (item.status === 'info' && (
                item.message.includes('开始处理') || 
                item.message.includes('正在处理') ||
                item.message.includes('等待')
            )) ||
            item.status === 'processing'
        );
        
        // 检查是否处理完成
        const isCompleted = data.status && data.status.some(item => 
            item.status === 'success' && (
                item.message.includes('处理完成') ||
                item.message.includes('数据已保存')
            )
        );
        
        // 如果还在处理中且没有完成，继续轮询
        if (isProcessing && !isCompleted) {
            setTimeout(pollStatus, 2000);
        } else if (isCompleted) {
            console.log('处理已完成，停止轮询');
            // 确保下载按钮可见
            downloadContainer.style.display = 'block';
        } else {
            // 如果既不在处理也没完成，可能是出错了，但仍然检查一次下载
            setTimeout(() => {
                downloadContainer.style.display = 'block';
            }, 1000);
        }
        
    } catch (error) {
        console.error('获取状态时出错:', error);
        
        // 任何错误都认为可能是处理完成，显示下载按钮
        downloadContainer.style.display = 'block';
        statusContainer.innerHTML += `<div class="status-item status-info">⚠️ 状态查询异常，如果之前显示了成功消息，请尝试下载</div>`;
        
        // 停止轮询，避免重复错误
        return;
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
    // 显示下载状态
    statusContainer.innerHTML += `<div class="status-item status-info">🔄 开始下载...</div>`;
    
    try {
        // 优先使用内存下载（最可靠的方法）
        console.log('🔄 尝试内存下载...');
        statusContainer.innerHTML += `<div class="status-item status-info">📥 尝试内存下载...</div>`;
        
        const memoryResponse = await fetch(`${API_BASE_URL}/download-memory`);
        
        if (memoryResponse.ok) {
            const contentType = memoryResponse.headers.get('content-type');
            console.log('内存下载响应类型:', contentType);
            
            if (contentType && contentType.includes('sheet')) {
                const blob = await memoryResponse.blob();
                console.log('获取到blob，大小:', blob.size);
                
                if (blob.size > 1000) { // 确保文件有内容
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = '小红书达人数据.xlsx';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    statusContainer.innerHTML += `<div class="status-item status-success">✅ 内存下载成功！文件大小: ${(blob.size/1024).toFixed(1)}KB</div>`;
                    return;
                }
            }
        }
        
        // 如果内存下载失败，尝试其他方法
        console.log('内存下载失败，尝试其他方法...');
        const secondaryResponse = await fetch(`${API_BASE_URL}/download`);
        
        if (secondaryResponse.ok && secondaryResponse.headers.get('content-type')?.includes('sheet')) {
            const blob = await secondaryResponse.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '小红书达人数据.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // 显示成功消息
            statusContainer.innerHTML += `<div class="status-item status-success">✅ 通过文件下载成功！</div>`;
            return;
        }
        
        // 最后尝试Base64下载
        console.log('内存下载失败，尝试Base64下载...');
        const base64Response = await fetch(`${API_BASE_URL}/download-base64`);
        const base64Data = await base64Response.json();
        
        if (base64Data.success) {
            // 将Base64转换为Blob并下载
            const byteCharacters = atob(base64Data.data);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { 
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
            });
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = base64Data.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            statusContainer.innerHTML += `<div class="status-item status-success">✅ 通过Base64下载成功！</div>`;
            return;
        }
        
        // 所有方法都失败了
        const errorData = base64Data.error || '所有下载方式都失败了';
        alert(`下载失败: ${errorData}`);
        
    } catch (error) {
        console.error('下载文件时出错:', error);
        alert(`下载文件时出错: ${error.message}`);
    }
}

// 上传 Excel 文件
async function uploadExcelFile() {
    const file = excelUpload.files[0];
    if (!file) {
        alert('请选择一个 Excel 文件');
        return;
    }
    
    // 验证文件类型
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        alert('请上传 Excel 文件 (.xlsx 或 .xls)');
        return;
    }
    
    // 获取列名
    const column = columnInput.value.trim() || 'A';
    if (!/^[A-Za-z]$/.test(column)) {
        alert('请输入有效的列字母 (A-Z)');
        return;
    }
    
    try {
        uploadExcelBtn.disabled = true;
        uploadExcelBtn.textContent = '上传中...';
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('column', column);
        
        const response = await fetch(`${API_BASE_URL}/upload-excel`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            statusContainer.innerHTML = `<div class="status-item status-error">${data.error}</div>`;
        } else {
            // 显示状态卡片
            statusCard.style.display = 'block';
            statusContainer.innerHTML = '<div class="status-item status-info">Excel 文件已上传，正在处理...</div>';
            
            // 开始轮询状态
            pollStatus();
        }
    } catch (error) {
        console.error('上传 Excel 文件时出错:', error);
        statusContainer.innerHTML = `<div class="status-item status-error">上传 Excel 文件时出错: ${error.message}</div>`;
    } finally {
        uploadExcelBtn.disabled = false;
        uploadExcelBtn.textContent = '上传并处理';
    }
} 

// 更新Cookie
async function updateCookie() {
    const cookieString = cookieInput.value.trim();
    if (!cookieString) {
        alert('请输入Cookie字符串');
        return;
    }
    
    try {
        updateCookieBtn.disabled = true;
        updateCookieBtn.textContent = '更新中...';
        
        const formData = new FormData();
        formData.append('cookie_string', cookieString);
        
        const response = await fetch(`${API_BASE_URL}/update-cookie`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            cookieStatus.innerHTML = `<div class="status-item status-error">${data.error}</div>`;
        } else {
            cookieStatus.innerHTML = `<div class="status-item status-success">${data.message}</div>`;
            setTimeout(() => {
                cookieStatus.innerHTML = '';
            }, 3000);
        }
    } catch (error) {
        console.error('更新Cookie时出错:', error);
        cookieStatus.innerHTML = `<div class="status-item status-error">更新Cookie时出错: ${error.message}</div>`;
    } finally {
        updateCookieBtn.disabled = false;
        updateCookieBtn.textContent = '更新Cookie';
    }
}

// 获取当前Cookie
async function getCurrentCookie() {
    try {
        getCurrentCookieBtn.disabled = true;
        getCurrentCookieBtn.textContent = '获取中...';
        
        const response = await fetch(`${API_BASE_URL}/get-cookie`);
        const data = await response.json();
        
        if (data.error) {
            cookieStatus.innerHTML = `<div class="status-item status-error">${data.error}</div>`;
        } else {
            cookieInput.value = data.cookie_string;
            cookieStatus.innerHTML = `<div class="status-item status-success">当前Cookie已显示在输入框中</div>`;
            setTimeout(() => {
                cookieStatus.innerHTML = '';
            }, 3000);
        }
    } catch (error) {
        console.error('获取Cookie时出错:', error);
        cookieStatus.innerHTML = `<div class="status-item status-error">获取Cookie时出错: ${error.message}</div>`;
    } finally {
        getCurrentCookieBtn.disabled = false;
        getCurrentCookieBtn.textContent = '查看当前Cookie';
    }
} 

// 验证Cookie状态
async function validateCookie() {
    try {
        validateCookieBtn.disabled = true;
        validateCookieBtn.textContent = '验证中...';
        
        const response = await fetch(`${API_BASE_URL}/validate-cookie`);
        const data = await response.json();
        
        if (data.error) {
            cookieStatus.innerHTML = `<div class="status-item status-error">${data.error}</div>`;
            cookieInfo.style.display = 'none';
        } else {
            // 显示验证结果
            const validityClass = data.is_valid === true ? 'status-success' : 
                                 data.is_valid === false ? 'status-error' : 'status-warning';
            const validityText = data.is_valid === true ? 'Cookie有效' : 
                                data.is_valid === false ? 'Cookie已过期或无效' : 'Cookie状态未知';
            
            cookieStatus.innerHTML = `<div class="status-item ${validityClass}">${validityText}</div>`;
            
            // 显示详细信息
            displayCookieInfo(data);
        }
    } catch (error) {
        console.error('验证Cookie时出错:', error);
        cookieStatus.innerHTML = `<div class="status-item status-error">验证Cookie时出错: ${error.message}</div>`;
    } finally {
        validateCookieBtn.disabled = false;
        validateCookieBtn.textContent = '验证Cookie状态';
    }
}

// 显示Cookie详细信息
function displayCookieInfo(data) {
    let infoHtml = '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px;">';
    infoHtml += '<h4 style="margin-bottom: 10px; color: #495057;">Cookie 详细信息</h4>';
    
    const cookieInfo = data.cookie_info;
    
    // 显示重要提示
    if (cookieInfo.important_note) {
        infoHtml += `<div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin-bottom: 15px; border-left: 4px solid #ffc107;">`;
        infoHtml += `<strong>${cookieInfo.important_note}</strong>`;
        infoHtml += '</div>';
    }
    
    // 显示API测试结果
    if (data.test_results && data.test_results.length > 0) {
        infoHtml += '<h5 style="margin-bottom: 8px;">API测试结果:</h5>';
        infoHtml += '<ul style="margin-bottom: 15px;">';
        data.test_results.forEach(test => {
            const statusColor = test.success ? '#28a745' : test.unauthorized ? '#dc3545' : '#ffc107';
            const statusIcon = test.success ? '✅' : test.unauthorized ? '❌' : '⚠️';
            infoHtml += `<li style="color: ${statusColor};">${statusIcon} ${test.endpoint}: ${test.status_code || test.error}</li>`;
        });
        infoHtml += '</ul>';
    }
    
    if (data.test_message) {
        infoHtml += `<p><strong>测试结果:</strong> ${data.test_message}</p>`;
    }
    
    // 显示loadts信息
    if (cookieInfo.loadts_readable) {
        infoHtml += `<p><strong>会话时间:</strong> ${cookieInfo.loadts_readable}</p>`;
        if (cookieInfo.loadts_note) {
            infoHtml += `<p style="font-size: 0.9em; color: #6c757d;">${cookieInfo.loadts_note}</p>`;
        }
    }
    
    // 显示会话令牌
    if (cookieInfo.session_tokens && cookieInfo.session_tokens.length > 0) {
        infoHtml += '<h5 style="margin-bottom: 8px; margin-top: 15px;">重要会话令牌:</h5><ul>';
        cookieInfo.session_tokens.forEach(token => {
            infoHtml += `<li><code>${token.key}</code>: ${token.prefix} (长度: ${token.length})</li>`;
        });
        infoHtml += '</ul>';
    }
    
    // 显示获取真实过期时间的方法
    if (cookieInfo.how_to_get_real_expiry) {
        infoHtml += '<h5 style="margin-bottom: 8px; margin-top: 15px;">如何获取真实过期时间:</h5>';
        cookieInfo.how_to_get_real_expiry.forEach(tip => {
            infoHtml += `<p style="font-size: 0.9em; margin-bottom: 5px;">${tip}</p>`;
        });
    }
    
    infoHtml += '</div>';
    
    cookieInfo.innerHTML = infoHtml;
    cookieInfo.style.display = 'block';
} 