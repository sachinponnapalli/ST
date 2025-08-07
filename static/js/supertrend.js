
function showNotification(message, type = 'success') {
    const container = document.querySelector('.notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Choose icon based on type
    const icon = type === 'success' ? '✨' : '⚠️';
    
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${icon}</span>
            <p class="notification-message">${message}</p>
            <button class="notification-close">×</button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Auto-remove notification after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'notifySlideOut 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
  
    // Handle close button
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'notifySlideOut 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    });
  }






function formatReadableDate(isoString, locale = 'en-US', use24Hour = false) {
    const date = new Date(isoString);

    const options = {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: !use24Hour
    };

    return date.toLocaleString(locale, options);
}

function update_pnl(){
    fetch(`/update_rsi_pnl/?version=${version}&curr_emulation=${curr_emulation}`)
	.then(res => res.json())
        .then(pnl => {
            pnl_val = (pnl["PNL"])
            $("#pnl").text(pnl_val.toFixed(2)).css("color", pnl["PNL"] >= 0 ? "#00e900" : "#f50000");
            $("#entry-ltp").text(`${pnl["ltp"]}`)
            $("#entry-symbol").text(`${pnl["tsym"]}`)
        })
}
// update_pnl()
// setInterval(update_pnl, 2000);

function convertTimestampToReadable(ts) {
    // Multiply by 1000 to convert seconds to milliseconds
    const date = new Date(ts * 1000);

    // Format the date to a readable string
    return date.toLocaleString(); // Returns in local format, e.g., "7/24/2025, 5:15:00 PM"
}


function update_orderbook(){
    fetch(`/update-rsi-orderbook/`)
	.then(res => res.json())
        .then(orderbook => {
            console.log("orderbook data")
            console.log(orderbook)

            latest_ob_entry = orderbook.at(-1)
            
      
           $("#orderbook_data").html("")

            orderbook.forEach(ele => {

            $("#orderbook_data").append(`
                <tr>
                    <td>${ convertTimestampToReadable( ele['ordenttm'])    }</td>
                    <td>${ele['tsym']}</td>
                    <td>${ele['s_prdt_ali']}</td>
                    <td>${ele['trantype']}</td>
                    <td>${ele['qty']}</td>
                    <td>${ ele['avgprc']== undefined ?  "NA" :   ele['avgprc']  }</td>
                    <td>${ele['prctyp']}</td>
                    <td>${ele['remarks']}</td>
                    <td>${ele['status']}</td>
                    
                </tr>`);
        });



        })
}
update_orderbook()
// setInterval(update_orderbook, 2000);



function formatReadableDate(isoString, locale = 'en-US', use24Hour = false) {
    const date = new Date(isoString);

    const options = {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: !use24Hour
    };

    return date.toLocaleString(locale, options);
}





function stats(){
  fetch(`/stats/`)
	.then(res => res.json())
        .then(stats => {
            if(stats['status'] == "success"){

                $("#stat_time").text(formatReadableDate(stats['data']['datetime']))
                $("#stat_open").text(stats['data']['open'])
                $("#stat_high").text(stats['data']['high'])
                $("#stat_low").text(stats['data']['low'])
                $("#stat_close").text(stats['data']['close'])
                $("#stat_supertrend").text(stats['data']['supertrend'])
                $("#stat_trend").text(stats['data']['trend'] == 1 ? "BULLISH" : "BEARISH")
                $("#stat_trade").text(stats['data']['trade'])
            }
            else{
                $("#stat_time").text("NA");  
                $("#stat_open").text("NA")
                $("#stat_high").text("NA")
                $("#stat_low").text("NA")
                $("#stat_close").text("NA")
                $("#stat_supertrend").text("NA")
                $("#stat_trend").text("NA")
                $("#stat_trade").text("NA")
            }
        })}

stats()




function update_candle_data(){
  fetch(`/latest-candle-data/`)
	.then(res => res.json())
        .then(stats => {
            if(stats['status'] == "success"){

                $("#latest_candle_time").text(formatReadableDate(stats['data']['datetime']))
                $("#latest_candle_open").text(stats['data']['open'])
                $("#latest_candle_high").text(stats['data']['high'])
                $("#latest_candle_low").text(stats['data']['low'])
                $("#latest_candle_close").text(stats['data']['close'])
            }
            else{
                $("#latest_candle_time").text("NA");  
                $("#latest_candle_open").text("NA")
                $("#latest_candle_high").text("NA")
                $("#latest_candle_low").text("NA")
                $("#latest_candle_close").text("NA")
            }
        })}

update_candle_data()
// setInterval(stats, 2000);







// Dark mode toggle functionality
      const toggleSwitch = document.querySelector("#checkbox");
      const currentTheme = localStorage.getItem("theme");

      if (currentTheme) {
        document.documentElement.setAttribute("data-theme", currentTheme);
        if (currentTheme === "dark") {
          toggleSwitch.checked = true;
        }
      }

      function switchTheme(e) {
        if (e.target.checked) {
          document.documentElement.setAttribute("data-theme", "dark");
          localStorage.setItem("theme", "dark");
        } else {
          document.documentElement.setAttribute("data-theme", "light");
          localStorage.setItem("theme", "light");
        }
      }
      
      toggleSwitch.addEventListener("change", switchTheme);





function updateConfig() {
    const button = document.querySelector(".submit-btn");
    
    // Disable button and apply styles
    button.disabled = true;
    button.style.opacity = "0.1";
    button.style.cursor = "default";

    const formData = new FormData(document.getElementById("updateForm"));
   
    // Update the configuration and leverage together
   
    fetch("/update_config/", {
        method: "POST",
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.success) {
            showNotification(data.message, 'success');
        } else {
            showNotification(data.message , 'error');
        }
        setTimeout(function() {
        button.disabled = false;
        button.style.opacity = "";
        button.style.cursor = "";
      }, 5000);
    })
    .catch((error) => {
        console.error("Error updating config:", error);
        showNotification('Error updating configuration', 'error');
    });
}



