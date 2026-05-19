document.getElementById('checkout-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btn = document.getElementById('checkout-btn');
    const statusDiv = document.getElementById('status-message');
    
    // Reset state
    btn.classList.add('loading');
    statusDiv.className = 'hidden';
    
    try {
        const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userId: document.getElementById('userId').value,
                cartTotal: 450.75,
                event: "USER_CHECKOUT"
            })
        });

        const data = await response.json();
        
        btn.classList.remove('loading');
        
        if (response.ok) {
            statusDiv.textContent = '🎉 Payment Successful! Event published to AWS.';
            statusDiv.className = 'show success';
            
            // Add a subtle success animation to the container
            const container = document.querySelector('.checkout-container');
            container.style.boxShadow = '0 30px 60px -12px rgba(16, 185, 129, 0.3)';
            setTimeout(() => {
                container.style.boxShadow = '';
            }, 2000);
            
        } else {
            throw new Error(data.error || 'Failed to process checkout');
        }
        
    } catch (error) {
        btn.classList.remove('loading');
        statusDiv.textContent = '❌ Error: ' + error.message;
        statusDiv.className = 'show error';
    }
});
