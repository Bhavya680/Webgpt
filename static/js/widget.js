(function() {
    // 1. Configuration
    const script = document.currentScript || document.querySelector('script[data-bot-id]');
    const botId = script ? script.getAttribute('data-bot-id') : null;
    const backendUrl = "http://localhost:8000"; // Update this for production
    
    if (!botId) {
        console.error("SiteBot: No data-bot-id found on the script tag.");
        return;
    }

    // 2. Styles
    const styles = `
        #sitebot-widget-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 999999;
            font-family: 'Inter', sans-serif;
        }
        #sitebot-fab {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: #4F46E5;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        #sitebot-fab:hover {
            transform: scale(1.1);
        }
        #sitebot-fab:active {
            transform: scale(0.95);
        }
        #sitebot-fab svg {
            width: 28px;
            height: 28px;
            fill: white;
        }
        #sitebot-iframe-container {
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 400px;
            height: 600px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 12px 24px rgba(0,0,0,0.1);
            overflow: hidden;
            display: none;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            border: 1px solid rgba(0,0,0,0.05);
        }
        #sitebot-iframe-container.active {
            display: block;
            opacity: 1;
            transform: translateY(0);
        }
        @media (max-width: 480px) {
            #sitebot-iframe-container {
                width: calc(100vw - 40px);
                height: calc(100vh - 120px);
            }
        }
    `;

    // 3. Inject DOM
    const styleSheet = document.createElement("style");
    styleSheet.innerText = styles;
    document.head.appendChild(styleSheet);

    const container = document.createElement("div");
    container.id = "sitebot-widget-container";
    container.innerHTML = `
        <div id="sitebot-iframe-container">
            <iframe id="sitebot-iframe" src="${backendUrl}/dashboard/bots/${botId}/widget/" 
                    style="width: 100%; height: 100%; border: none;"></iframe>
        </div>
        <div id="sitebot-fab">
            <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
        </div>
    `;
    document.body.appendChild(container);

    // 4. Toggle Logic
    const fab = document.getElementById("sitebot-fab");
    const iframeContainer = document.getElementById("sitebot-iframe-container");
    let isOpen = false;

    function toggleWidget(forceClose = false) {
        if (forceClose) isOpen = false;
        else isOpen = !isOpen;

        if (isOpen) {
            iframeContainer.style.display = "block";
            setTimeout(() => iframeContainer.classList.add("active"), 10);
            fab.innerHTML = `<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>`;
        } else {
            iframeContainer.classList.remove("active");
            setTimeout(() => iframeContainer.style.display = "none", 300);
            fab.innerHTML = `<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>`;
        }
    }

    fab.onclick = () => toggleWidget();

    // Listen for close message from iframe
    window.addEventListener("message", (event) => {
        if (event.data === "close-sitebot") {
            toggleWidget(true);
        }
    });
})();
