# الاتصال عبر WebSockets

[**تجد كل شيفرة هذا الفصل هنا**](https://github.com/quii/learn-go-with-tests/tree/main/websockets)

سنتعلم في هذا الفصل كيف نستعمل WebSockets لتحسين تطبيقنا.

## ملخص المشروع

لدينا تطبيقان في قاعدة شيفرة البوكر

- *تطبيق سطر الأوامر*. يطلب من المستخدم إدخال عدد اللاعبين في اللعبة. ومن ثم يبلّغ اللاعبين بقيمة "الرهان الأعمى" التي تزداد مع الوقت. وفي أي لحظة يستطيع المستخدم إدخال `"{Playername} wins"` لإنهاء اللعبة وتسجيل الفائز في مخزن.
- *تطبيق الويب*. يتيح للمستخدمين تسجيل الفائزين في المباريات، ويعرض جدول الدوري. ويتشارك المخزن نفسه مع تطبيق سطر الأوامر.

## الخطوات التالية

مالكة المنتج سعيدة جداً بتطبيق سطر الأوامر، لكنها تفضّل لو استطعنا نقل تلك الوظيفة إلى المتصفح. فهي تتخيل صفحة ويب فيها مربع نصي يتيح للمستخدم إدخال عدد اللاعبين، وحين يرسل النموذج تعرض الصفحة قيمة الرهان الأعمى وتحدّثها تلقائياً عند الحاجة. وكما في تطبيق سطر الأوامر، يستطيع المستخدم إعلان الفائز فيُحفظ في قاعدة البيانات.

للوهلة الأولى يبدو الأمر بسيطاً جداً، لكن كالعادة علينا التشديد على اتباع أسلوب _تكراري_ في كتابة البرمجيات.

أولاً سنحتاج إلى تقديم HTML. فحتى الآن أعادت كل نقاط نهاية HTTP لدينا إما نصاً عادياً أو JSON. _يمكننا_ استعمال الأساليب نفسها التي نعرفها (فكلها في النهاية سلاسل نصية)، لكن يمكننا أيضاً استعمال الحزمة [html/template](https://golang.org/pkg/html/template/) للحصول على حل أنظف.

ونحتاج أيضاً إلى أن نستطيع إرسال الرسائل إلى المستخدم بشكل غير متزامن، تقول `The blind is now *y*`، دون الحاجة إلى تحديث المتصفح. ويمكننا استعمال [WebSockets](https://en.wikipedia.org/wiki/WebSocket) لتسهيل ذلك.

> بروتوكول WebSocket بروتوكول اتصالات حاسوبية يوفر قنوات اتصال ثنائية الاتجاه بالكامل عبر اتصال TCP واحد

بما أننا نتناول عدداً من الأساليب، فمن الأهم أن ننجز أصغر قدر من العمل المفيد أولاً ثم نتقدم خطوة خطوة.

لهذا السبب، أول ما سنفعله هو إنشاء صفحة ويب فيها نموذج يسجّل فيه المستخدم الفائز. وبدلاً من استعمال نموذج عادي، سنستعمل WebSockets لإرسال تلك البيانات إلى خادمنا ليسجلها.

بعد ذلك سنعمل على تنبيهات الرهان الأعمى، وعندها سيكون لدينا قدر من شيفرة البنية التحتية جاهزاً.

### وماذا عن اختبارات JavaScript؟

سنكتب بعض شيفرة JavaScript لفعل هذا، لكنني لن أتطرق إلى كتابة اختبارات لها.

هذا ممكن بالطبع، لكن اختصاراً لن أضمّن أي شرح لذلك.

آسف يا أصدقاء. اضغطوا على O'Reilly ليدفعوا لي كي أكتب "تعلّم JavaScript بالاختبارات".

## اكتب الاختبار أولاً

أول ما علينا فعله هو تقديم بعض HTML للمستخدمين حين يصلون إلى `/game`.

إليك تذكيراً بالشيفرة (code) ذات الصلة في خادم الويب لدينا

```go
type PlayerServer struct {
	store PlayerStore
	http.Handler
}

const jsonContentType = "application/json"

func NewPlayerServer(store PlayerStore) *PlayerServer {
	p := new(PlayerServer)

	p.store = store

	router := http.NewServeMux()
	router.Handle("/league", http.HandlerFunc(p.leagueHandler))
	router.Handle("/players/", http.HandlerFunc(p.playersHandler))

	p.Handler = router

	return p
}
```

_أسهل_ ما يمكننا فعله الآن هو التحقق من أننا حين نرسل `GET /game` نحصل على `200`.

```go
func TestGame(t *testing.T) {
	t.Run("GET /game returns 200", func(t *testing.T) {
		server := NewPlayerServer(&StubPlayerStore{})

		request, _ := http.NewRequest(http.MethodGet, "/game", nil)
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertStatus(t, response.Code, http.StatusOK)
	})
}
```

## حاول تشغيل الاختبار

```
--- FAIL: TestGame (0.00s)
=== RUN   TestGame/GET_/game_returns_200
    --- FAIL: TestGame/GET_/game_returns_200 (0.00s)
    	server_test.go:109: did not get correct status, got 404, want 200
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

لدى خادمنا موجِّه مُعدّ، لذا فإصلاح هذا سهل نسبياً.

أضف إلى موجِّهنا

```go
router.Handle("/game", http.HandlerFunc(p.game))
```

ثم اكتب الطريقة (method) `game`

```go
func (p *PlayerServer) game(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
}
```

## أعد الهيكلة

شيفرة الخادم جيدة بالفعل، لأننا أدرجنا مزيداً من الشيفرة في الشيفرة الحالية جيدة الهيكلة بسهولة كبيرة.

يمكننا ترتيب الاختبار (test) قليلاً بإضافة دالة مساعدة للاختبار `newGameRequest` لإرسال الطلب إلى `/game`. حاول كتابتها بنفسك.

```go
func TestGame(t *testing.T) {
	t.Run("GET /game returns 200", func(t *testing.T) {
		server := NewPlayerServer(&StubPlayerStore{})

		request := newGameRequest()
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertStatus(t, response, http.StatusOK)
	})
}
```

ستلاحظ أيضاً أنني غيّرت `assertStatus` لتقبل `response` بدلاً من `response.Code`، لأنني أشعر أنها تُقرأ أفضل.

علينا الآن جعل نقطة النهاية تعيد بعض HTML، وإليك ذلك

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Let's play poker</title>
</head>
<body>
<section id="game">
    <div id="declare-winner">
        <label for="winner">Winner</label>
        <input type="text" id="winner"/>
        <button id="winner-button">Declare winner</button>
    </div>
</section>
</body>
<script type="application/javascript">

    const submitWinnerButton = document.getElementById('winner-button')
    const winnerInput = document.getElementById('winner')

    if (window['WebSocket']) {
        const conn = new WebSocket('ws://' + document.location.host + '/ws')

        submitWinnerButton.onclick = event => {
            conn.send(winnerInput.value)
        }
    }
</script>
</html>
```

لدينا صفحة ويب بسيطة جداً

 - حقل إدخال نصي يُدخل فيه المستخدم الفائز
 - زر يستطيع النقر عليه لإعلان الفائز.
 - بعض شيفرة JavaScript لفتح اتصال WebSocket بخادمنا ومعالجة الضغط على زر الإرسال

الكائن `WebSocket` مدمج في معظم المتصفحات الحديثة، لذا لا نحتاج إلى القلق بشأن جلب أي مكتبات. ولن تعمل صفحة الويب في المتصفحات الأقدم، لكن لا بأس بذلك في هذا السيناريو.

### كيف نختبر أننا نعيد الترميز الصحيح؟

هناك بضع طرق. وكما شددنا في الكتاب كله، من المهم أن تكون للاختبارات التي تكتبها قيمة كافية لتبرير تكلفتها.

1. اكتب اختباراً قائماً على المتصفح، باستعمال شيء مثل Selenium. وهذه الاختبارات أكثر الأساليب "واقعية"، لأنها تشغّل متصفح ويب فعلياً من نوع ما وتحاكي مستخدماً يتفاعل معه. وقد تمنحك هذه الاختبارات ثقة كبيرة بأن نظامك يعمل، لكنها أصعب كتابة من اختبارات الوحدة وأبطأ تشغيلاً بكثير. ولأغراض منتجنا فهذا مبالغة.
2. أجرِ مطابقة دقيقة للسلسلة النصية. هذا _قد_ يكون مقبولاً، لكن هذا النوع من الاختبارات ينتهي به الأمر إلى أن يكون هشاً جداً. ففي اللحظة التي يغيّر فيها أحدهم الترميز سيفشل لديك اختبار، مع أن شيئاً لم _يتعطل فعلاً_ من الناحية العملية.
3. تحقق من أننا نستدعي القالب الصحيح. سنستعمل مكتبة قوالب من المكتبة القياسية لتقديم HTML (سنناقشها بعد قليل)، ويمكننا حقن _الشيء_ الذي يولّد HTML والتجسس على استدعائه للتحقق من أننا نفعل ذلك بشكل صحيح. وسيكون لهذا أثر في تصميم شيفرتنا، لكنه لا يختبر الكثير فعلاً، سوى أننا نستدعيه بملف القالب الصحيح. وبما أنه لن يكون لدينا إلا قالب واحد في مشروعنا، فيبدو احتمال الفشل هنا ضئيلاً.

لذا للمرة الأولى في كتاب "تعلّم غو بالاختبارات"، لن نكتب اختباراً.

ضع الترميز في ملف باسم `game.html`

بعد ذلك غيّر نقطة النهاية التي كتبناها للتو إلى ما يلي

```go
func (p *PlayerServer) game(w http.ResponseWriter, r *http.Request) {
	tmpl, err := template.ParseFiles("game.html")

	if err != nil {
		http.Error(w, fmt.Sprintf("problem loading template %s", err.Error()), http.StatusInternalServerError)
		return
	}

	tmpl.Execute(w, nil)
}
```

الحزمة [`html/template`](https://golang.org/pkg/html/template/) حزمة في غو (Go) لإنشاء HTML. وفي حالتنا نستدعي `template.ParseFiles` ونعطيها مسار ملف HTML. وبافتراض عدم وجود خطأ (error)، يمكنك بعد ذلك تنفيذ القالب بـ`Execute`، فيكتبه إلى `io.Writer`. ونريد في حالتنا أن يكتبه بـ`Write` إلى الإنترنت، لذا نعطيه `http.ResponseWriter`.

بما أننا لم نكتب اختباراً، فمن الحكمة اختبار خادم الويب يدوياً للتأكد من أن الأشياء تعمل كما نأمل. اذهب إلى `cmd/webserver` وشغّل الملف `main.go`. وزُر `http://localhost:5000/game`.

_ينبغي_ أن يكون قد ظهر لك خطأ عن عدم القدرة على إيجاد القالب. فيمكنك إما تغيير المسار ليكون نسبياً إلى مجلدك، أو وضع نسخة من `game.html` في المجلد `cmd/webserver`. وقد اخترت إنشاء رابط رمزي (`ln -s ../../game.html game.html`) إلى الملف داخل جذر المشروع، كي تنعكس أي تغييرات أجريها حين أشغّل الخادم.

إن أجريت هذا التغيير وشغّلت مجدداً، فينبغي أن ترى واجهة المستخدم لدينا.

علينا الآن اختبار أننا حين نتلقى سلسلة نصية عبر اتصال WebSocket بخادمنا، نعلنها فائزةً في مباراة.

## اكتب الاختبار أولاً

للمرة الأولى سنستعمل مكتبة خارجية كي نستطيع العمل مع اتصالات WebSockets بسهولة.

شغّل `go get github.com/gorilla/websocket`

سيجلب هذا شيفرة مكتبة [Gorilla WebSocket](https://github.com/gorilla/websocket) الممتازة. ويمكننا الآن تحديث اختباراتنا لمتطلبنا الجديد.

```go
t.Run("when we get a message over a websocket it is a winner of a game", func(t *testing.T) {
	store := &StubPlayerStore{}
	winner := "Ruth"
	server := httptest.NewServer(NewPlayerServer(store))
	defer server.Close()

	wsURL := "ws" + strings.TrimPrefix(server.URL, "http") + "/ws"

	ws, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Fatalf("could not open a ws connection on %s %v", wsURL, err)
	}
	defer ws.Close()

	if err := ws.WriteMessage(websocket.TextMessage, []byte(winner)); err != nil {
		t.Fatalf("could not send message over ws connection %v", err)
	}

	AssertPlayerWin(t, store, winner)
})
```

تأكد من وجود استيراد للمكتبة `websocket`. فقد فعلت بيئة التطوير لدي ذلك تلقائياً، وكذلك ينبغي أن تفعل بيئتك.

لاختبار ما يحدث من المتصفح، علينا فتح اتصال WebSocket خاص بنا والكتابة إليه.

كانت اختباراتنا السابقة حول الخادم تستدعي فقط طرقاً على خادمنا، لكننا نحتاج الآن إلى اتصال دائم بخادمنا. ولفعل ذلك نستعمل `httptest.NewServer` التي تأخذ `http.Handler` وتشغّله وتستمع إلى الاتصالات.

باستعمال `websocket.DefaultDialer.Dial` نحاول الاتصال بخادمنا، ثم سنحاول إرسال رسالة فيها `winner`.

وأخيراً، نؤكد على مخزن اللاعبين للتحقق من أن الفائز قد سُجّل.

## حاول تشغيل الاختبار

```
=== RUN   TestGame/when_we_get_a_message_over_a_websocket_it_is_a_winner_of_a_game
    --- FAIL: TestGame/when_we_get_a_message_over_a_websocket_it_is_a_winner_of_a_game (0.00s)
        server_test.go:124: could not open a ws connection on ws://127.0.0.1:55838/ws websocket: bad handshake
```

لم نغيّر خادمنا ليقبل اتصالات WebSocket على `/ws`، لذا لم تحدث المصافحة بعد.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

أضف مدخلاً آخر إلى موجِّهنا

```go
router.Handle("/ws", http.HandlerFunc(p.webSocket))
```

ثم أضف المعالج (handler) الجديد `webSocket`

```go
func (p *PlayerServer) webSocket(w http.ResponseWriter, r *http.Request) {
	upgrader := websocket.Upgrader{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
	}
	upgrader.Upgrade(w, r, nil)
}
```

لقبول اتصال WebSocket نرقّي الطلب بـ`Upgrade`. وإن أعدت تشغيل الاختبار الآن، فينبغي أن تنتقل إلى الخطأ التالي.

```
=== RUN   TestGame/when_we_get_a_message_over_a_websocket_it_is_a_winner_of_a_game
    --- FAIL: TestGame/when_we_get_a_message_over_a_websocket_it_is_a_winner_of_a_game (0.00s)
        server_test.go:132: got 0 calls to RecordWin want 1
```

والآن بعد أن صار لدينا اتصال مفتوح، سنريد الاستماع إلى رسالة ثم تسجيلها كفائز.

```go
func (p *PlayerServer) webSocket(w http.ResponseWriter, r *http.Request) {
	upgrader := websocket.Upgrader{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
	}
	conn, _ := upgrader.Upgrade(w, r, nil)
	_, winnerMsg, _ := conn.ReadMessage()
	p.store.RecordWin(string(winnerMsg))
}
```

(نعم، نتجاهل كثيراً من الأخطاء الآن!)

تحجب `conn.ReadMessage()` منتظرةً رسالة على الاتصال. وبمجرد أن نتلقى واحدة، نستعملها في `RecordWin`. وهذا سيغلق في النهاية اتصال WebSocket القائم.

إن حاولت تشغيل الاختبار، فما زال يفشل.

المشكلة في التوقيت. فهناك تأخير بين قراءة اتصال WebSocket للرسالة وتسجيل الفوز، وينتهي اختبارنا قبل أن يحدث ذلك. ويمكنك اختبار هذا بوضع `time.Sleep` قصيرة قبل التوكيد الأخير.

لنمضِ بذلك الآن، مع الإقرار بأن وضع فترات نوم اعتباطية في الاختبارات **ممارسة سيئة جداً**.

```go
time.Sleep(10 * time.Millisecond)
AssertPlayerWin(t, store, winner)
```

## أعد الهيكلة

ارتكبنا خطايا كثيرة لجعل هذا الاختبار يعمل، في شيفرة الخادم وشيفرة الاختبار معاً، لكن تذكّر أن هذه أسهل طريقة لنا للعمل.

لدينا برنامج قبيح وفظيع لكنه _يعمل_ ومدعوم باختبار، لذا نحن الآن أحرار في جعله جميلاً، عالمين أننا لن نُفسد شيئاً عن غير قصد.

لنبدأ بشيفرة الخادم.

يمكننا نقل `upgrader` إلى قيمة خاصة داخل حزمتنا، لأننا لا نحتاج إلى إعادة التصريح عنه مع كل طلب اتصال WebSocket

```go
var wsUpgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

func (p *PlayerServer) webSocket(w http.ResponseWriter, r *http.Request) {
	conn, _ := wsUpgrader.Upgrade(w, r, nil)
	_, winnerMsg, _ := conn.ReadMessage()
	p.store.RecordWin(string(winnerMsg))
}
```

سيعمل استدعاؤنا لـ`template.ParseFiles("game.html")` مع كل `GET /game`، مما يعني أننا سنذهب إلى نظام الملفات مع كل طلب، مع أنه لا حاجة إلى إعادة تحليل القالب. لنُعِد هيكلة شيفرتنا بحيث نحلل القالب مرة واحدة في `NewPlayerServer` بدلاً من ذلك. وسنضطر إلى جعل هذه الدالة (function) قادرة الآن على إعادة خطأ في حال واجهنا مشكلات في جلب القالب من القرص أو تحليله.

إليك التغييرات ذات الصلة في `PlayerServer`

```go
type PlayerServer struct {
	store PlayerStore
	http.Handler
	template *template.Template
}

const htmlTemplatePath = "game.html"

func NewPlayerServer(store PlayerStore) (*PlayerServer, error) {
	p := new(PlayerServer)

	tmpl, err := template.ParseFiles(htmlTemplatePath)

	if err != nil {
		return nil, fmt.Errorf("problem opening %s %v", htmlTemplatePath, err)
	}

	p.template = tmpl
	p.store = store

	router := http.NewServeMux()
	router.Handle("/league", http.HandlerFunc(p.leagueHandler))
	router.Handle("/players/", http.HandlerFunc(p.playersHandler))
	router.Handle("/game", http.HandlerFunc(p.game))
	router.Handle("/ws", http.HandlerFunc(p.webSocket))

	p.Handler = router

	return p, nil
}

func (p *PlayerServer) game(w http.ResponseWriter, r *http.Request) {
	p.template.Execute(w, nil)
}
```

بتغيير توقيع `NewPlayerServer` صارت لدينا الآن مشكلات تصريف. حاول إصلاحها بنفسك، أو ارجع إلى الشيفرة المصدرية إن واجهت صعوبة.

في شيفرة الاختبار صنعت دالة مساعدة باسم `mustMakePlayerServer(t *testing.T, store PlayerStore) *PlayerServer` كي أخفي ضجيج الأخطاء عن الاختبارات.

```go
func mustMakePlayerServer(t *testing.T, store PlayerStore) *PlayerServer {
	server, err := NewPlayerServer(store)
	if err != nil {
		t.Fatal("problem creating player server", err)
	}
	return server
}
```

وبالمثل، أنشأت دالة مساعدة أخرى `mustDialWS` كي أخفي ضجيج الأخطاء المزعج عند إنشاء اتصال WebSocket جديد.

```go
func mustDialWS(t *testing.T, url string) *websocket.Conn {
	ws, _, err := websocket.DefaultDialer.Dial(url, nil)

	if err != nil {
		t.Fatalf("could not open a ws connection on %s %v", url, err)
	}

	return ws
}
```

وأخيراً، يمكننا في شيفرة الاختبار إنشاء دالة مساعدة لترتيب إرسال الرسائل

```go
func writeWSMessage(t testing.TB, conn *websocket.Conn, message string) {
	t.Helper()
	if err := conn.WriteMessage(websocket.TextMessage, []byte(message)); err != nil {
		t.Fatalf("could not send message over ws connection %v", err)
	}
}
```

والآن بعد أن نجحت الاختبارات، جرّب تشغيل الخادم وإعلان بعض الفائزين في `/game`. ينبغي أن تراهم مسجّلين في `/league`. وتذكّر أننا في كل مرة نحصل فيها على فائز _نغلق الاتصال_، لذا ستحتاج إلى تحديث الصفحة لفتح الاتصال مجدداً.

صنعنا نموذج ويب بسيطاً يتيح للمستخدمين تسجيل الفائز في مباراة. لنتقدم فيه بحيث يستطيع المستخدم بدء لعبة بتقديم عدد اللاعبين، ويدفع الخادم رسائل إلى العميل يبلّغه فيها بقيمة الرهان الأعمى مع مرور الوقت.

أولاً حدّث `game.html` لتحديث شيفرة جانب العميل للمتطلبات الجديدة

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Lets play poker</title>
</head>
<body>
<section id="game">
    <div id="game-start">
        <label for="player-count">Number of players</label>
        <input type="number" id="player-count"/>
        <button id="start-game">Start</button>
    </div>

    <div id="declare-winner">
        <label for="winner">Winner</label>
        <input type="text" id="winner"/>
        <button id="winner-button">Declare winner</button>
    </div>

    <div id="blind-value"/>
</section>

<section id="game-end">
    <h1>Another great game of poker everyone!</h1>
    <p><a href="/league">Go check the league table</a></p>
</section>

</body>
<script type="application/javascript">
    const startGame = document.getElementById('game-start')

    const declareWinner = document.getElementById('declare-winner')
    const submitWinnerButton = document.getElementById('winner-button')
    const winnerInput = document.getElementById('winner')

    const blindContainer = document.getElementById('blind-value')

    const gameContainer = document.getElementById('game')
    const gameEndContainer = document.getElementById('game-end')

    declareWinner.hidden = true
    gameEndContainer.hidden = true

    document.getElementById('start-game').addEventListener('click', event => {
        startGame.hidden = true
        declareWinner.hidden = false

        const numberOfPlayers = document.getElementById('player-count').value

        if (window['WebSocket']) {
            const conn = new WebSocket('ws://' + document.location.host + '/ws')

            submitWinnerButton.onclick = event => {
                conn.send(winnerInput.value)
                gameEndContainer.hidden = false
                gameContainer.hidden = true
            }

            conn.onclose = evt => {
                blindContainer.innerText = 'Connection closed'
            }

            conn.onmessage = evt => {
                blindContainer.innerText = evt.data
            }

            conn.onopen = function () {
                conn.send(numberOfPlayers)
            }
        }
    })
</script>
</html>
```

التغييرات الأساسية هي إضافة قسم لإدخال عدد اللاعبين، وقسم لعرض قيمة الرهان الأعمى. ولدينا قليل من المنطق لإظهار واجهة المستخدم أو إخفائها بحسب مرحلة اللعبة.

أي رسالة نتلقاها عبر `conn.onmessage` نفترض أنها تنبيهات بالرهان الأعمى، لذا نضبط `blindContainer.innerText` وفقاً لذلك.

كيف نرسل تنبيهات الرهان الأعمى؟ في الفصل السابق قدّمنا فكرة `Game` كي تستطيع شيفرة سطر الأوامر استدعاء `Game`، ويُعتنى بكل شيء آخر، بما في ذلك جدولة تنبيهات الرهان الأعمى. وقد تبيّن أن هذا فصل جيد للاهتمامات.

```go
type Game interface {
	Start(numberOfPlayers int)
	Finish(winner string)
}
```

حين كان المستخدم يُطلب منه عدد اللاعبين في `CLI`، كانت تبدأ اللعبة بـ`Start`، فتنطلق تنبيهات الرهان الأعمى، وحين يعلن المستخدم الفائز تنتهي بـ`Finish`. وهذه المتطلبات نفسها التي لدينا الآن، لكن بطريقة مختلفة للحصول على المدخلات؛ لذا ينبغي أن نسعى إلى إعادة استعمال هذا المفهوم إن استطعنا.

تنفيذنا "الحقيقي" لـ`Game` هو `TexasHoldem`

```go
type TexasHoldem struct {
	alerter BlindAlerter
	store   PlayerStore
}
```

بإرسال `BlindAlerter` يستطيع `TexasHoldem` جدولة تنبيهات الرهان الأعمى لتُرسل إلى _أي مكان_

```go
type BlindAlerter interface {
	ScheduleAlertAt(duration time.Duration, amount int)
}
```

وللتذكير، إليك تنفيذنا لـ`BlindAlerter` الذي نستعمله في `CLI`.

```go
func StdOutAlerter(duration time.Duration, amount int) {
	time.AfterFunc(duration, func() {
		fmt.Fprintf(os.Stdout, "Blind is now %d\n", amount)
	})
}
```

هذا يعمل في `CLI` لأننا _نريد دائماً إرسال التنبيهات إلى `os.Stdout`_، لكنه لن يعمل مع خادم الويب. ففي كل طلب نحصل على `http.ResponseWriter` جديد نرقّيه بعد ذلك إلى `*websocket.Conn`. لذا لا يمكننا أن نعرف عند بناء تبعياتنا إلى أين ينبغي أن تذهب تنبيهاتنا.

لهذا السبب علينا تغيير `BlindAlerter.ScheduleAlertAt` بحيث يأخذ وجهة للتنبيهات، كي نستطيع إعادة استعماله في خادم الويب.

افتح `blind_alerter.go` وأضف المعامل (parameter) من النوع `io.Writer`

```go
type BlindAlerter interface {
	ScheduleAlertAt(duration time.Duration, amount int, to io.Writer)
}

type BlindAlerterFunc func(duration time.Duration, amount int, to io.Writer)

func (a BlindAlerterFunc) ScheduleAlertAt(duration time.Duration, amount int, to io.Writer) {
	a(duration, amount, to)
}
```

فكرة `StdoutAlerter` لا تناسب نموذجنا الجديد، لذا غيّر اسمه إلى `Alerter` فحسب

```go
func Alerter(duration time.Duration, amount int, to io.Writer) {
	time.AfterFunc(duration, func() {
		fmt.Fprintf(to, "Blind is now %d\n", amount)
	})
}
```

إن حاولت التصريف، فسيفشل في `TexasHoldem` لأنه يستدعي `ScheduleAlertAt` دون وجهة. ولجعل الأشياء تُصرَّف مجدداً _في الوقت الحالي_، ثبّت الوجهة على `os.Stdout`.

حاول تشغيل الاختبارات، وستفشل لأن `SpyBlindAlerter` لم يعد يحقق `BlindAlerter`. أصلح ذلك بتحديث توقيع `ScheduleAlertAt`، ثم شغّل الاختبارات، وينبغي أن نظل في الأخضر.

ليس من المنطقي أن يعرف `TexasHoldem` إلى أين يرسل تنبيهات الرهان الأعمى. لنحدّث الآن `Game` بحيث تعلن حين تبدأ اللعبة _إلى أين_ ينبغي أن تذهب التنبيهات.

```go
type Game interface {
	Start(numberOfPlayers int, alertsDestination io.Writer)
	Finish(winner string)
}
```

دع المصرِّف (compiler) يخبرك بما عليك إصلاحه. والتغيير ليس سيئاً جداً:

- حدّث `TexasHoldem` بحيث يحقق `Game` كما ينبغي
- في `CLI` حين نبدأ اللعبة، مرّر الخاصية `out` (`cli.game.Start(numberOfPlayers, cli.out)`)
- في اختبار `TexasHoldem` أستعمل `game.Start(5, io.Discard)` لإصلاح مشكلة التصريف، وضبط مخرجات التنبيه لتُهمَل

إن فعلت كل شيء بشكل صحيح، فينبغي أن يكون كل شيء أخضر! ويمكننا الآن محاولة استعمال `Game` داخل `Server`.

## اكتب الاختبار أولاً

متطلبات `CLI` و`Server` واحدة! كل ما في الأمر أن آلية التوصيل مختلفة.

لنلقِ نظرة على اختبار `CLI` لنستلهم منه.

```go
t.Run("start game with 3 players and finish game with 'Chris' as winner", func(t *testing.T) {
	game := &GameSpy{}

	out := &bytes.Buffer{}
	in := userSends("3", "Chris wins")

	poker.NewCLI(in, out, game).PlayPoker()

	assertMessagesSentToUser(t, out, poker.PlayerPrompt)
	assertGameStartedWith(t, game, 3)
	assertFinishCalledWith(t, game, "Chris")
})
```

يبدو أننا ينبغي أن نستطيع استخلاص نتيجة مشابهة بالاختبار باستعمال `GameSpy`

استبدل اختبار websocket القديم بما يلي

```go
t.Run("start a game with 3 players and declare Ruth the winner", func(t *testing.T) {
	game := &poker.GameSpy{}
	winner := "Ruth"
	server := httptest.NewServer(mustMakePlayerServer(t, dummyPlayerStore, game))
	ws := mustDialWS(t, "ws"+strings.TrimPrefix(server.URL, "http")+"/ws")

	defer server.Close()
	defer ws.Close()

	writeWSMessage(t, ws, "3")
	writeWSMessage(t, ws, winner)

	time.Sleep(10 * time.Millisecond)
	assertGameStartedWith(t, game, 3)
	assertFinishCalledWith(t, game, winner)
})
```

- كما ناقشنا، ننشئ جاسوساً من `Game` ونمرره إلى `mustMakePlayerServer` (تأكد من تحديث الدالة المساعدة لتدعم ذلك).
- ثم نرسل رسائل web socket الخاصة بلعبة.
- وأخيراً نؤكد أن اللعبة بدأت وانتهت بما نتوقع.

## حاول تشغيل الاختبار

ستظهر لك عدة أخطاء تصريف حول `mustMakePlayerServer` في اختبارات أخرى. قدّم متغيراً غير مُصدَّر باسم `dummyGame` واستعمله في كل الاختبارات التي لا تُصرَّف

```go
var (
	dummyGame = &GameSpy{}
)
```

الخطأ الأخير حيث نحاول تمرير `Game` إلى `NewPlayerServer` الذي لا يدعمه بعد

```
./server_test.go:21:38: too many arguments in call to "github.com/quii/learn-go-with-tests/WebSockets/v2".NewPlayerServer
	have ("github.com/quii/learn-go-with-tests/WebSockets/v2".PlayerStore, "github.com/quii/learn-go-with-tests/WebSockets/v2".Game)
	want ("github.com/quii/learn-go-with-tests/WebSockets/v2".PlayerStore)
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

أضفه فقط كوسيط (argument) في الوقت الحالي لمجرد جعل الاختبار يعمل

```go
func NewPlayerServer(store PlayerStore, game Game) (*PlayerServer, error)
```

أخيراً!

```
=== RUN   TestGame/start_a_game_with_3_players_and_declare_Ruth_the_winner
--- FAIL: TestGame (0.01s)
    --- FAIL: TestGame/start_a_game_with_3_players_and_declare_Ruth_the_winner (0.01s)
    	server_test.go:146: wanted Start called with 3 but got 0
    	server_test.go:147: expected finish called with 'Ruth' but got ''
FAIL
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

علينا إضافة `Game` كحقل في `PlayerServer` كي يستطيع استعماله حين تصله الطلبات.

```go
type PlayerServer struct {
	store PlayerStore
	http.Handler
	template *template.Template
	game     Game
}
```

(لدينا بالفعل طريقة اسمها `game`، لذا غيّر اسمها إلى `playGame`)

بعد ذلك لنسنده في الدالة البانية

```go
func NewPlayerServer(store PlayerStore, game Game) (*PlayerServer, error) {
	p := new(PlayerServer)

	tmpl, err := template.ParseFiles(htmlTemplatePath)

	if err != nil {
		return nil, fmt.Errorf("problem opening %s %v", htmlTemplatePath, err)
	}

	p.game = game

	// etc
}
```

يمكننا الآن استعمال `Game` داخل `webSocket`.

```go
func (p *PlayerServer) webSocket(w http.ResponseWriter, r *http.Request) {
	conn, _ := wsUpgrader.Upgrade(w, r, nil)

	_, numberOfPlayersMsg, _ := conn.ReadMessage()
	numberOfPlayers, _ := strconv.Atoi(string(numberOfPlayersMsg))
	p.game.Start(numberOfPlayers, io.Discard) //todo: Don't discard the blinds messages!

	_, winner, _ := conn.ReadMessage()
	p.game.Finish(string(winner))
}
```

رائع! تنجح الاختبارات.

لن نرسل رسائل الرهان الأعمى إلى أي مكان _بعد_، لأننا نحتاج إلى التفكير في ذلك. فحين نستدعي `game.Start` نرسل `io.Discard`، الذي يُهمل أي رسائل تُكتب إليه فحسب.

في الوقت الحالي شغّل خادم الويب. ستحتاج إلى تحديث `main.go` لتمرير `Game` إلى `PlayerServer`

```go
func main() {
	db, err := os.OpenFile(dbFileName, os.O_RDWR|os.O_CREATE, 0666)

	if err != nil {
		log.Fatalf("problem opening %s %v", dbFileName, err)
	}

	store, err := poker.NewFileSystemPlayerStore(db)

	if err != nil {
		log.Fatalf("problem creating file system player store, %v ", err)
	}

	game := poker.NewTexasHoldem(poker.BlindAlerterFunc(poker.Alerter), store)

	server, err := poker.NewPlayerServer(store, game)

	if err != nil {
		log.Fatalf("problem creating player server %v", err)
	}

	log.Fatal(http.ListenAndServe(":5000", server))
}
```

بغض النظر عن أننا لا نحصل على تنبيهات الرهان الأعمى بعد، فالتطبيق يعمل! فقد استطعنا إعادة استعمال `Game` مع `PlayerServer`، وتولى كل التفاصيل. وبمجرد أن نعرف كيف نرسل تنبيهات الرهان الأعمى إلى web sockets بدلاً من إهمالها، _ينبغي_ أن يعمل كل شيء.

لكن قبل ذلك، لنرتب بعض الشيفرة.

## أعد الهيكلة

طريقة استعمالنا لـWebSockets بسيطة إلى حد ما، ومعالجة الأخطاء ساذجة إلى حد ما، لذا أردت تغليف ذلك في نوع (type) لإزالة هذه الفوضى من شيفرة الخادم. وقد نرغب في العودة إليها لاحقاً، لكن هذا سيرتب الأمور قليلاً في الوقت الحالي

```go
type playerServerWS struct {
	*websocket.Conn
}

func newPlayerServerWS(w http.ResponseWriter, r *http.Request) *playerServerWS {
	conn, err := wsUpgrader.Upgrade(w, r, nil)

	if err != nil {
		log.Printf("problem upgrading connection to WebSockets %v\n", err)
	}

	return &playerServerWS{conn}
}

func (w *playerServerWS) WaitForMsg() string {
	_, msg, err := w.ReadMessage()
	if err != nil {
		log.Printf("error reading from websocket %v\n", err)
	}
	return string(msg)
}
```

والآن صارت شيفرة الخادم أبسط قليلاً

```go
func (p *PlayerServer) webSocket(w http.ResponseWriter, r *http.Request) {
	ws := newPlayerServerWS(w, r)

	numberOfPlayersMsg := ws.WaitForMsg()
	numberOfPlayers, _ := strconv.Atoi(numberOfPlayersMsg)
	p.game.Start(numberOfPlayers, io.Discard) //todo: Don't discard the blinds messages!

	winner := ws.WaitForMsg()
	p.game.Finish(winner)
}
```

بمجرد أن نعرف كيف لا نهمل رسائل الرهان الأعمى، ننتهي.

### لـ_نمتنع_ عن كتابة اختبار!

أحياناً حين لا نكون متأكدين من كيفية فعل شيء ما، يكون من الأفضل أن نعبث ونجرّب الأشياء! تأكد من إيداع عملك أولاً، لأننا بمجرد أن نجد طريقة ينبغي أن نقودها عبر اختبار.

سطر الشيفرة الإشكالي لدينا هو

```go
p.game.Start(numberOfPlayers, io.Discard) //todo: Don't discard the blinds messages!
```

علينا تمرير `io.Writer` لتكتب اللعبة تنبيهات الرهان الأعمى إليه.

ألن يكون جميلاً لو استطعنا تمرير `playerServerWS` من قبل؟ إنه غلافنا حول WebSocket، لذا _يبدو_ أننا ينبغي أن نستطيع إرساله إلى `Game` ليرسل الرسائل إليه.

جرّب ذلك:

```go
func (p *PlayerServer) webSocket(w http.ResponseWriter, r *http.Request) {
	ws := newPlayerServerWS(w, r)

	numberOfPlayersMsg := ws.WaitForMsg()
	numberOfPlayers, _ := strconv.Atoi(numberOfPlayersMsg)
	p.game.Start(numberOfPlayers, ws)
	//etc...
}
```

يعترض المصرِّف

```
./server.go:71:14: cannot use ws (type *playerServerWS) as type io.Writer in argument to p.game.Start:
	*playerServerWS does not implement io.Writer (missing Write method)
```

يبدو أن الشيء البديهي الذي ينبغي فعله هو جعل `playerServerWS` _يحقق_ `io.Writer` فعلاً. ولفعل ذلك نستعمل `*websocket.Conn` الأساسي لاستعمال `WriteMessage` لإرسال الرسالة عبر websocket

```go
func (w *playerServerWS) Write(p []byte) (n int, err error) {
	err = w.WriteMessage(websocket.TextMessage, p)

	if err != nil {
		return 0, err
	}

	return len(p), nil
}
```

يبدو هذا سهلاً أكثر من اللازم! حاول تشغيل التطبيق وانظر إن كان يعمل.

قبل ذلك عدّل `TexasHoldem` بحيث يكون وقت زيادة الرهان الأعمى أقصر، كي تراه عملياً

```go
blindIncrement := time.Duration(5+numberOfPlayers) * time.Second // (rather than a minute)
```

ينبغي أن تراه يعمل! فمقدار الرهان الأعمى يزداد في المتصفح كأنه السحر.

لنتراجع الآن عن الشيفرة ونفكر في كيفية اختبارها. فلكي _ننفّذها_، كل ما فعلناه هو أننا مررنا إلى `StartGame` القيمة `playerServerWS` بدلاً من `io.Discard`، وقد يدفعك هذا إلى التفكير في أن علينا ربما التجسس على الاستدعاء للتحقق من أنه يعمل.

التجسس رائع ويساعدنا على التحقق من تفاصيل التنفيذ، لكن ينبغي أن نحاول دائماً تفضيل اختبار السلوك _الحقيقي_ إن استطعنا، لأنك حين تقرر إعادة الهيكلة تكون اختبارات التجسس غالباً هي التي تبدأ بالفشل، إذ إنها تتحقق عادةً من تفاصيل التنفيذ التي تحاول تغييرها.

يفتح اختبارنا حالياً اتصال websocket بخادمنا قيد التشغيل، ويرسل رسائل لجعله يفعل أشياء. وبالقدر نفسه ينبغي أن نستطيع اختبار الرسائل التي يعيدها خادمنا عبر اتصال websocket ذاته.

## اكتب الاختبار أولاً

سنعدّل اختبارنا الحالي.

حالياً لا يرسل `GameSpy` أي بيانات إلى `out` حين تستدعي `Start`. وينبغي أن نغيّره بحيث نستطيع ضبطه لإرسال رسالة جاهزة، ثم نتحقق من أن تلك الرسالة تُرسل إلى websocket. وهذا ينبغي أن يمنحنا الثقة بأننا ضبطنا الأشياء بشكل صحيح، مع الاستمرار في اختبار السلوك الحقيقي الذي نريده.

```go
type GameSpy struct {
	StartCalled     bool
	StartCalledWith int
	BlindAlert      []byte

	FinishedCalled   bool
	FinishCalledWith string
}
```

أضف الحقل `BlindAlert`.

حدّث `Start` في `GameSpy` لترسل الرسالة الجاهزة إلى `out`.

```go
func (g *GameSpy) Start(numberOfPlayers int, out io.Writer) {
	g.StartCalled = true
	g.StartCalledWith = numberOfPlayers
	out.Write(g.BlindAlert)
}
```

هذا يعني الآن أننا حين نختبر `PlayerServer` فإنه حين يحاول بدء اللعبة بـ`Start` ينبغي أن ينتهي به الأمر إلى إرسال رسائل عبر websocket إن كانت الأشياء تعمل بشكل صحيح.

وأخيراً، يمكننا تحديث الاختبار

```go
t.Run("start a game with 3 players, send some blind alerts down WS and declare Ruth the winner", func(t *testing.T) {
	wantedBlindAlert := "Blind is 100"
	winner := "Ruth"

	game := &GameSpy{BlindAlert: []byte(wantedBlindAlert)}
	server := httptest.NewServer(mustMakePlayerServer(t, dummyPlayerStore, game))
	ws := mustDialWS(t, "ws"+strings.TrimPrefix(server.URL, "http")+"/ws")

	defer server.Close()
	defer ws.Close()

	writeWSMessage(t, ws, "3")
	writeWSMessage(t, ws, winner)

	time.Sleep(10 * time.Millisecond)
	assertGameStartedWith(t, game, 3)
	assertFinishCalledWith(t, game, winner)

	_, gotBlindAlert, _ := ws.ReadMessage()

	if string(gotBlindAlert) != wantedBlindAlert {
		t.Errorf("got blind alert %q, want %q", string(gotBlindAlert), wantedBlindAlert)
	}
})
```

- أضفنا `wantedBlindAlert`، وضبطنا `GameSpy` لإرساله إلى `out` إن استُدعيت `Start`.
- نأمل أن يُرسل عبر اتصال websocket، لذا أضفنا استدعاء لـ`ws.ReadMessage()` لانتظار إرسال رسالة ثم التحقق من أنها التي توقعناها.

## حاول تشغيل الاختبار

ستجد أن الاختبار يتجمد إلى الأبد. وذلك لأن `ws.ReadMessage()` ستُحجب حتى تتلقى رسالة، وهو ما لن يحدث أبداً.


## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

لا ينبغي أبداً أن تكون لدينا اختبارات تتجمد، لذا لنقدّم طريقة للتعامل مع الشيفرة التي نريد أن تنتهي مهلتها.

```go
func within(t testing.TB, d time.Duration, assert func()) {
	t.Helper()

	done := make(chan struct{}, 1)

	go func() {
		assert()
		done <- struct{}{}
	}()

	select {
	case <-time.After(d):
		t.Error("timed out")
	case <-done:
	}
}
```

ما تفعله `within` هو أخذ دالة `assert` كوسيط، ثم تشغيلها في `goroutine`. وإن انتهت الدالة، وحين تنتهي، فستشير إلى انتهائها عبر القناة `done`.

وبينما يحدث ذلك نستعمل تعليمة `select` التي تتيح لنا انتظار أن ترسل قناة رسالة. ومن هنا يكون سباقاً بين الدالة `assert` و`time.After`، التي سترسل إشارة حين تنقضي المدة.

وأخيراً، صنعت دالة مساعدة للتوكيد لمجرد جعل الأشياء أكثر ترتيباً

```go
func assertWebsocketGotMsg(t *testing.T, ws *websocket.Conn, want string) {
	_, msg, _ := ws.ReadMessage()
	if string(msg) != want {
		t.Errorf(`got "%s", want "%s"`, string(msg), want)
	}
}
```

إليك كيف يُقرأ الاختبار الآن

```go
t.Run("start a game with 3 players, send some blind alerts down WS and declare Ruth the winner", func(t *testing.T) {
	wantedBlindAlert := "Blind is 100"
	winner := "Ruth"

	game := &GameSpy{BlindAlert: []byte(wantedBlindAlert)}
	server := httptest.NewServer(mustMakePlayerServer(t, dummyPlayerStore, game))
	ws := mustDialWS(t, "ws"+strings.TrimPrefix(server.URL, "http")+"/ws")

	defer server.Close()
	defer ws.Close()

	writeWSMessage(t, ws, "3")
	writeWSMessage(t, ws, winner)

	time.Sleep(tenMS)

	assertGameStartedWith(t, game, 3)
	assertFinishCalledWith(t, game, winner)
	within(t, tenMS, func() { assertWebsocketGotMsg(t, ws, wantedBlindAlert) })
})
```

والآن إن شغّلت الاختبار...

```
=== RUN   TestGame
=== RUN   TestGame/start_a_game_with_3_players,_send_some_blind_alerts_down_WS_and_declare_Ruth_the_winner
--- FAIL: TestGame (0.02s)
    --- FAIL: TestGame/start_a_game_with_3_players,_send_some_blind_alerts_down_WS_and_declare_Ruth_the_winner (0.02s)
    	server_test.go:143: timed out
    	server_test.go:150: got "", want "Blind is 100"
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

وأخيراً، يمكننا الآن تغيير شيفرة الخادم، بحيث يرسل اتصال WebSocket إلى اللعبة حين تبدأ

```go
func (p *PlayerServer) webSocket(w http.ResponseWriter, r *http.Request) {
	ws := newPlayerServerWS(w, r)

	numberOfPlayersMsg := ws.WaitForMsg()
	numberOfPlayers, _ := strconv.Atoi(numberOfPlayersMsg)
	p.game.Start(numberOfPlayers, ws)

	winner := ws.WaitForMsg()
	p.game.Finish(winner)
}
```

## أعد الهيكلة

كانت شيفرة الخادم تغييراً صغيراً جداً، لذا ليس هناك الكثير مما يمكن تغييره هنا، لكن شيفرة الاختبار ما زال فيها استدعاء `time.Sleep`، لأن علينا انتظار خادمنا ليؤدي عمله بشكل غير متزامن.

يمكننا إعادة هيكلة الدالتين المساعدتين `assertGameStartedWith` و`assertFinishCalledWith` بحيث تستطيعان إعادة محاولة توكيداتهما لفترة قصيرة قبل الفشل.

إليك كيف يمكنك فعل ذلك لـ`assertFinishCalledWith`، ويمكنك استعمال الأسلوب نفسه للدالة المساعدة الأخرى.

```go
func assertFinishCalledWith(t testing.TB, game *GameSpy, winner string) {
	t.Helper()

	passed := retryUntil(500*time.Millisecond, func() bool {
		return game.FinishCalledWith == winner
	})

	if !passed {
		t.Errorf("expected finish called with %q but got %q", winner, game.FinishCalledWith)
	}
}
```

إليك كيف عُرّفت `retryUntil`

```go
func retryUntil(d time.Duration, f func() bool) bool {
	deadline := time.Now().Add(d)
	for time.Now().Before(deadline) {
		if f() {
			return true
		}
	}
	return false
}
```

## الخلاصة

اكتمل تطبيقنا الآن. فيمكن بدء لعبة بوكر عبر متصفح ويب، ويُبلَّغ المستخدمون بقيمة الرهان الأعمى مع مرور الوقت عبر WebSockets. وحين تنتهي اللعبة يستطيعون تسجيل الفائز، فيُحفظ باستعمال شيفرة كتبناها قبل بضعة فصول. ويستطيع اللاعبون معرفة من هو أفضل (أو أكثر) لاعبي البوكر حظاً باستعمال نقطة النهاية `/league` في الموقع.

ارتكبنا أخطاء خلال الرحلة، لكن مع تدفق `TDD` لم نبتعد كثيراً أبداً عن برنامج يعمل. وكنا أحراراً في مواصلة التقدم والتجريب.

سيعيد الفصل الأخير النظر في الأسلوب، والتصميم الذي وصلنا إليه، ويحسم بعض المسائل المعلقة.

تناولنا بعض الأشياء في هذا الفصل

### الاتصال عبر WebSockets

- وسيلة مريحة لإرسال الرسائل بين العملاء والخوادم دون أن يضطر العميل إلى الاستعلام من الخادم باستمرار. وشيفرة العميل والخادم لدينا بسيطة جداً.
- اختبارها بسيط، لكن عليك الحذر من الطبيعة غير المتزامنة للاختبارات

### التعامل في الاختبارات مع الشيفرة التي قد تتأخر أو لا تنتهي أبداً

- أنشئ دوالاً مساعدة لإعادة محاولة التوكيدات وإضافة مهل زمنية.
- يمكننا استعمال `goroutines` لضمان ألا تحجب التوكيدات أي شيء، ثم استعمال القنوات لنتيح لها الإشارة إلى أنها انتهت أم لا.
- في الحزمة `time` بعض الدوال المفيدة التي ترسل أيضاً إشارات عبر القنوات عن أحداث في الزمن، كي نستطيع ضبط المهل الزمنية
