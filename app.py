Samajh gaya, ab tumhara actual code dikh gaya. Maine ye dekha: simple Flask app hai, ek hi system prompt hai, Groq ka llama-3.3-70b-versatile model use ho raha hai, aur chat_history ek global list hai.

Maine mode-switching add karke updated app.py banaya hai — har mode ka apna system prompt aur apni alag chat history hogi, aur "thinking" mode ke liye Groq ka reasoning model (gpt-oss-120b) use hoga jo extra deeply sochta hai.

Isko apne GitHub repo mein purane app.py ki jagah daal do. Kaise kaam karta hai:

- Frontend se `/chat` par message ke saath `mode` bhejna hai: `"study"`, `"creator"`, `"coding"`, `"thinking"`, ya default `"assistant"`.
- Har mode ki apni alag chat history hai, taaki Study mode ki baatein Creator mode mein mix na ho.
- Image-to-answer ke liye `image_url` bhej do (base64 data URL ya hosted link) — wo automatically vision model use kar lega.
- Thinking mode automatically reasoning model (gpt-oss-120b) use karega, baki sab fast model pe rahenge.

Ek baat note kar lo: chat history abhi bhi sabhi visitors ke beech shared hai (no login/session system) — abhi ke liye theek hai, lekin jab real users aayenge to har user ki apni history honi chahiye. Wo baad mein fix kar sakte hain.

Ab batao — chat.html mein mode-selector buttons (UI) banane ka kaam karein, ya pehle frontend se request bhejne wala JS code update karein?
