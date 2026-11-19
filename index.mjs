import makeWASocket, { DisconnectReason, useMultiFileAuthState, jidNormalizedUser} from '@whiskeysockets/baileys'
import qrcode from 'qrcode-terminal'

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys')

    const sock = makeWASocket({
        auth: state
    })

    sock.ev.on('creds.update', saveCreds)

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update
        if (qr) {
            qrcode.generate(qr, { small: true })
        }
        if (connection === 'close') {
            const shouldReconnect =
                lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut
            console.log('connection closed due to', lastDisconnect?.error, ', reconnecting:', shouldReconnect)
            if (shouldReconnect) {
                connectToWhatsApp()
            }
        } else if (connection === 'open') {
            console.log('opened connection')
        }
    })

    const seen = new Set()

sock.ev.on('messages.upsert', async ({ messages, type }) => {
    if (type !== 'notify') return

    const myIds = new Set(
        [sock.user?.id, sock.user?.lid, state.creds.me?.lid]
            .filter(Boolean)
            .map(jid => jidNormalizedUser(jid))
    )

    for (const m of messages) {
        const jid = m.key.remoteJid
        const id = m.key.id

        // Accept your own messages in a direct chat.
        if (!m.key.fromMe || !jid || !id) continue
        if (!/@(s\.whatsapp\.net|lid)$/.test(jid)) continue

        // Verify that the destination is your self-chat.
        const isSelfChat = [jid, m.key.remoteJidAlt]
            .filter(Boolean)
            .some(value => myIds.has(jidNormalizedUser(value)))

        if (!isSelfChat || seen.has(id)) continue

        const text =
            m.message?.conversation ??
            m.message?.extendedTextMessage?.text ??
            ''

        // Ignore ordinary notes.
        if (!/^!pc(?:\s|$)/.test(text)) continue
        seen.add(id)

        try {
            const command = text.slice(3).trim()
            if (!command) continue

            const response = await fetch('http://127.0.0.1:8200/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: command }),
                signal: AbortSignal.timeout(150000)
            })

            if (!response.ok) {
                throw new Error(`Python returned HTTP ${response.status}`)
            }

            const data = await response.json()

            await sock.sendMessage(jid, {
                text: `[Laptop] ${data.reply}`
            })
        } catch (error) {
            console.error('Request failed:', error.message)
        }
    }
})
}

connectToWhatsApp().catch(console.error)