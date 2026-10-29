# صيغة JSON والتوجيه والتضمين

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/json)**

[في الفصل السابق](http-server.md) أنشأنا خادم ويب يخزّن عدد المباريات التي فاز بها اللاعبون.

لدى مالكة المنتج متطلب جديد: نقطة نهاية جديدة اسمها `/league` تعيد قائمة بكل اللاعبين المخزّنين. وتريد أن تُعاد القائمة بصيغة JSON تحديداً.

## إليك الشيفرة التي لدينا حتى الآن

```go
// server.go
package main

import (
	"fmt"
	"net/http"
	"strings"
)

type PlayerStore interface {
	GetPlayerScore(name string) int
	RecordWin(name string)
}

type PlayerServer struct {
	store PlayerStore
}

func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")

	switch r.Method {
	case http.MethodPost:
		p.processWin(w, player)
	case http.MethodGet:
		p.showScore(w, player)
	}
}

func (p *PlayerServer) showScore(w http.ResponseWriter, player string) {
	score := p.store.GetPlayerScore(player)

	if score == 0 {
		w.WriteHeader(http.StatusNotFound)
	}

	fmt.Fprint(w, score)
}

func (p *PlayerServer) processWin(w http.ResponseWriter, player string) {
	p.store.RecordWin(player)
	w.WriteHeader(http.StatusAccepted)
}
```

```go
// in_memory_player_store.go
package main

func NewInMemoryPlayerStore() *InMemoryPlayerStore {
	return &InMemoryPlayerStore{map[string]int{}}
}

type InMemoryPlayerStore struct {
	store map[string]int
}

func (i *InMemoryPlayerStore) RecordWin(name string) {
	i.store[name]++
}

func (i *InMemoryPlayerStore) GetPlayerScore(name string) int {
	return i.store[name]
}

```

```go
// main.go
package main

import (
	"log"
	"net/http"
)

func main() {
	server := &PlayerServer{NewInMemoryPlayerStore()}
	log.Fatal(http.ListenAndServe(":5000", server))
}
```

يمكنك إيجاد الاختبارات المقابلة في الرابط أعلى الفصل.

سنبدأ بصنع نقطة النهاية الخاصة بجدول الدوري.

## اكتب الاختبار أولاً

سنوسّع المجموعة الحالية لأن لدينا فيها بعض دوال الاختبار المفيدة و`PlayerStore` مزيفاً نستعمله.

```go
//server_test.go
func TestLeague(t *testing.T) {
	store := StubPlayerStore{}
	server := &PlayerServer{&store}

	t.Run("it returns 200 on /league", func(t *testing.T) {
		request, _ := http.NewRequest(http.MethodGet, "/league", nil)
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertStatus(t, response.Code, http.StatusOK)
	})
}
```

قبل القلق بشأن النتائج الفعلية وJSON، سنحاول إبقاء التغييرات صغيرة مع خطة للتقدم تكرارياً نحو هدفنا. وأبسط بداية هي التحقق من أننا نستطيع الوصول إلى `/league` والحصول على `OK`.

## حاول تشغيل الاختبار

```
    --- FAIL: TestLeague/it_returns_200_on_/league (0.00s)
        server_test.go:101: status code is wrong: got 404, want 200
FAIL
FAIL	playerstore	0.221s
FAIL
```

يعيد `PlayerServer` لدينا `404 Not Found`، وكأننا نحاول الحصول على مرات فوز لاعب غير معروف. وبالنظر إلى كيفية تنفيذ `server.go` للطريقة `ServeHTTP`، ندرك أنه يفترض دائماً أنه يُستدعى بعنوان URL يشير إلى لاعب محدد:

```go
player := strings.TrimPrefix(r.URL.Path, "/players/")
```

ذكرنا في الفصل السابق أن هذه طريقة ساذجة إلى حد ما في التوجيه. ويخبرنا اختبارنا (test) بشكل صحيح أننا نحتاج إلى مفهوم للتعامل مع مسارات الطلبات المختلفة.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

لدى غو (Go) آلية توجيه مدمجة اسمها [`ServeMux`](https://golang.org/pkg/net/http/#ServeMux) (مُوزِّع الطلبات)، تتيح لك ربط قيم `http.Handler` بمسارات طلبات معيّنة.

لنرتكب بعض الخطايا ونجعل الاختبارات تنجح بأسرع طريقة ممكنة، عالمين أننا نستطيع إعادة الهيكلة بأمان بمجرد أن نعرف أن الاختبارات تنجح.

```go
//server.go
func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {

	router := http.NewServeMux()

	router.Handle("/league", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	router.Handle("/players/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		player := strings.TrimPrefix(r.URL.Path, "/players/")

		switch r.Method {
		case http.MethodPost:
			p.processWin(w, player)
		case http.MethodGet:
			p.showScore(w, player)
		}
	}))

	router.ServeHTTP(w, r)
}
```

- حين يبدأ الطلب ننشئ موجِّهاً، ثم نخبره أن يستعمل المعالج `y` للمسار `x`.
- فلنقطة النهاية الجديدة، نستعمل `http.HandlerFunc` و_دالة مجهولة_ تنفّذ `w.WriteHeader(http.StatusOK)` حين يُطلب `/league`، لجعل اختبارنا الجديد ينجح.
- وللمسار `/players/` نقص شيفرتنا ونلصقها في `http.HandlerFunc` أخرى.
- وأخيراً، نعالج الطلب الوارد باستدعاء `ServeHTTP` الخاصة بالموجِّه الجديد (هل لاحظت أن `ServeMux` هو _أيضاً_ `http.Handler`؟)

ينبغي أن تنجح الاختبارات الآن.

## أعد الهيكلة

تبدو `ServeHTTP` كبيرة إلى حد ما، ويمكننا فصل الأشياء قليلاً بإعادة هيكلة معالجاتنا (handlers) في طرق منفصلة.

```go
//server.go
func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {

	router := http.NewServeMux()
	router.Handle("/league", http.HandlerFunc(p.leagueHandler))
	router.Handle("/players/", http.HandlerFunc(p.playersHandler))

	router.ServeHTTP(w, r)
}

func (p *PlayerServer) leagueHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
}

func (p *PlayerServer) playersHandler(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")

	switch r.Method {
	case http.MethodPost:
		p.processWin(w, player)
	case http.MethodGet:
		p.showScore(w, player)
	}
}
```

من الغريب (وغير الكفء) إعداد موجِّه حين يصل الطلب ثم استدعاؤه. فما نريده في الوضع المثالي هو دالة (function) ما مثل `NewPlayerServer` تأخذ تبعياتنا وتجري الإعداد لمرة واحدة بإنشاء الموجِّه. ثم يستطيع كل طلب ببساطة استعمال تلك النسخة الواحدة من الموجِّه.

```go
//server.go
type PlayerServer struct {
	store  PlayerStore
	router *http.ServeMux
}

func NewPlayerServer(store PlayerStore) *PlayerServer {
	p := &PlayerServer{
		store,
		http.NewServeMux(),
	}

	p.router.Handle("/league", http.HandlerFunc(p.leagueHandler))
	p.router.Handle("/players/", http.HandlerFunc(p.playersHandler))

	return p
}

func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	p.router.ServeHTTP(w, r)
}
```

- صار `PlayerServer` يحتاج الآن إلى تخزين موجِّه.
- نقلنا إنشاء التوجيه من `ServeHTTP` إلى `NewPlayerServer`، فلا يلزم فعله إلا مرة واحدة، لا مع كل طلب.
- ستحتاج إلى تحديث كل شيفرة الاختبار والإنتاج التي كنا نكتب فيها `PlayerServer{&store}` لتصبح `NewPlayerServer(&store)`.

### إعادة هيكلة أخيرة

جرّب تغيير الشيفرة إلى ما يلي.

```go
type PlayerServer struct {
	store PlayerStore
	http.Handler
}

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

ثم استبدل `server := &PlayerServer{&store}` بـ`server := NewPlayerServer(&store)` في `server_test.go` و`server_integration_test.go` و`main.go`.

وأخيراً تأكد من **حذف** `func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request)` لأنها لم تعد لازمة!

## التضمين

غيّرنا الخاصية الثانية في `PlayerServer`، فحذفنا الخاصية المسماة `router http.ServeMux` واستبدلناها بـ`http.Handler`؛ وهذا يسمى _التضمين_ (embedding).

> لا توفر غو المفهوم المعتاد للتصنيف الفرعي المقاد بالأنواع، لكن لديها القدرة على "استعارة" أجزاء من تنفيذ ما بتضمين أنواع داخل بنية أو واجهة.

من كتاب [Effective Go: التضمين](https://golang.org/doc/effective_go.html#embedding)

معنى هذا أن `PlayerServer` صار لديه الآن كل الطرق التي لدى `http.Handler`، وهي `ServeHTTP` فقط.

ولـ"ملء" `http.Handler` نسنده إلى `router` الذي ننشئه في `NewPlayerServer`. ويمكننا فعل ذلك لأن `http.ServeMux` لديه الطريقة `ServeHTTP`.

وهذا يتيح لنا حذف طريقتنا `ServeHTTP`، لأننا نكشف واحدة بالفعل عبر النوع المضمَّن.

التضمين ميزة مثيرة للاهتمام جداً في اللغة. ويمكنك استعماله مع الواجهات لتركيب واجهات جديدة.

```go
type Animal interface {
	Eater
	Sleeper
}
```

ويمكنك استعماله مع الأنواع الملموسة أيضاً، لا الواجهات فقط. وكما تتوقع، إن ضمّنت نوعاً ملموساً فستصل إلى كل طرقه وحقوله العامة.

### أي عيوب؟

عليك الحذر عند تضمين الأنواع، لأنك ستكشف كل الطرق والحقول العامة للنوع الذي تضمّنه. وفي حالتنا لا بأس بذلك، لأننا ضمّنّا فقط _الواجهة_ التي أردنا كشفها (`http.Handler`).

لو تكاسلنا وضمّنّا `http.ServeMux` بدلاً منها (النوع الملموس)، لظلت الشيفرة تعمل، _لكن_ مستخدمي `PlayerServer` سيستطيعون إضافة مسارات جديدة إلى خادمنا لأن `Handle(path, handler)` ستكون عامة.

**حين تضمّن الأنواع، فكّر جيداً في أثر ذلك على واجهتك البرمجية العامة.**

من الأخطاء الشائعة _جداً_ إساءة استعمال التضمين، فينتهي الأمر بتلويث واجهاتك البرمجية وكشف دواخل نوعك.

والآن بعد أن أعدنا هيكلة تطبيقنا، يمكننا بسهولة إضافة مسارات جديدة، ولدينا بداية نقطة النهاية `/league`. وعلينا الآن جعلها تعيد بعض المعلومات المفيدة.

ينبغي أن نعيد بعض JSON يبدو شيئاً كهذا.

```json
[
   {
      "Name":"Bill",
      "Wins":10
   },
   {
      "Name":"Alice",
      "Wins":15
   }
]
```

## اكتب الاختبار أولاً

سنبدأ بمحاولة تحليل الاستجابة إلى شيء ذي معنى.

```go
//server_test.go
func TestLeague(t *testing.T) {
	store := StubPlayerStore{}
	server := NewPlayerServer(&store)

	t.Run("it returns 200 on /league", func(t *testing.T) {
		request, _ := http.NewRequest(http.MethodGet, "/league", nil)
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		var got []Player

		err := json.NewDecoder(response.Body).Decode(&got)

		if err != nil {
			t.Fatalf("Unable to parse response from server %q into slice of Player, '%v'", response.Body, err)
		}

		assertStatus(t, response.Code, http.StatusOK)
	})
}
```

### لماذا لا نختبر سلسلة JSON النصية؟

قد تقول إن خطوة أولى أبسط ستكون التوكيد فقط على أن متن الاستجابة يحتوي على سلسلة JSON معيّنة.

بحسب خبرتي، الاختبارات التي تؤكد على سلاسل JSON النصية تعاني المشكلات التالية.

- *الهشاشة*. إن غيّرت نموذج البيانات، فستفشل اختباراتك.
- *صعوبة التنقيح*. قد يكون من الصعب فهم المشكلة الفعلية عند مقارنة سلسلتي JSON.
- *ضعف التعبير عن القصد*. مع أن المخرجات ينبغي أن تكون JSON، فإن المهم حقاً هو ماهية البيانات بالضبط، لا طريقة ترميزها.
- *إعادة اختبار المكتبة القياسية*. لا حاجة إلى اختبار كيف تُخرج المكتبة القياسية JSON، فهي مختبَرة بالفعل. لا تختبر شيفرة الآخرين.

بل ينبغي أن نسعى إلى تحليل JSON إلى هياكل بيانات ذات صلة بما نختبره.

### نمذجة البيانات

بالنظر إلى نموذج بيانات JSON، يبدو أننا نحتاج إلى مصفوفة من `Player` فيها بعض الحقول، لذا أنشأنا نوعاً (type) جديداً لتجسيد ذلك.

```go
//server.go
type Player struct {
	Name string
	Wins int
}
```

### فك ترميز JSON

```go
//server_test.go
var got []Player
err := json.NewDecoder(response.Body).Decode(&got)
```

لتحليل JSON إلى نموذج بياناتنا، ننشئ `Decoder` من الحزمة `encoding/json` ثم نستدعي طريقته `Decode`. ولإنشاء `Decoder` يحتاج إلى `io.Reader` يقرأ منه، وهو في حالتنا `Body` الخاص بجاسوس الاستجابة.

تأخذ `Decode` عنوان الشيء الذي نحاول فك الترميز إليه، ولهذا نصرّح عن شريحة فارغة من `Player` في السطر السابق.

قد يفشل تحليل JSON، لذا قد تعيد `Decode` قيمة `error`. ولا فائدة من متابعة الاختبار إن فشل ذلك، لذا نتحقق من الخطأ ونوقف الاختبار بـ`t.Fatalf` إن حدث. ولاحظ أننا نطبع متن الاستجابة مع الخطأ، لأن من المهم لمن يشغّل الاختبار أن يرى السلسلة النصية التي لا يمكن تحليلها.

## حاول تشغيل الاختبار

```
=== RUN   TestLeague/it_returns_200_on_/league
    --- FAIL: TestLeague/it_returns_200_on_/league (0.00s)
        server_test.go:107: Unable to parse response from server '' into slice of Player, 'unexpected end of JSON input'
```

نقطة النهاية لدينا لا تعيد حالياً متناً، لذا لا يمكن تحليله كـJSON.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
//server.go
func (p *PlayerServer) leagueHandler(w http.ResponseWriter, r *http.Request) {
	leagueTable := []Player{
		{"Chris", 20},
	}

	json.NewEncoder(w).Encode(leagueTable)

	w.WriteHeader(http.StatusOK)
}
```

ينجح الاختبار الآن.

### الترميز وفك الترميز

لاحظ التناظر الجميل في المكتبة القياسية.

- لإنشاء `Encoder` تحتاج إلى `io.Writer`، وهو ما يحققه `http.ResponseWriter`.
- ولإنشاء `Decoder` تحتاج إلى `io.Reader`، وهو ما يحققه الحقل `Body` في جاسوس الاستجابة لدينا.

استعملنا `io.Writer` في هذا الكتاب كله، وهذا دليل آخر على انتشاره في المكتبة القياسية، وعلى سهولة عمل كثير من المكتبات معه.

## أعد الهيكلة

سيكون من الجميل تقديم فصل للاهتمامات بين معالجنا والحصول على `leagueTable`، لأننا نعرف أننا لن نُبقيه ثابتاً قريباً جداً.

```go
//server.go
func (p *PlayerServer) leagueHandler(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(p.getLeagueTable())
	w.WriteHeader(http.StatusOK)
}

func (p *PlayerServer) getLeagueTable() []Player {
	return []Player{
		{"Chris", 20},
	}
}
```

بعد ذلك، سنريد توسيع اختبارنا كي نتحكم بالضبط بالبيانات التي نريد استرجاعها.

## اكتب الاختبار أولاً

يمكننا تحديث الاختبار للتوكيد على أن جدول الدوري يحتوي على بعض اللاعبين الذين سنضعهم كبيانات ثابتة في مخزننا.

حدّث `StubPlayerStore` ليتيح له تخزين دوري، وهو مجرد شريحة (slice) من `Player`. وسنخزّن فيه بياناتنا المتوقعة.

```go
//server_test.go
type StubPlayerStore struct {
	scores   map[string]int
	winCalls []string
	league   []Player
}
```

بعد ذلك، حدّث اختبارنا الحالي بوضع بعض اللاعبين في خاصية الدوري في البديل الثابت، وأكّد أنهم يُعادون من خادمنا.

```go
//server_test.go
func TestLeague(t *testing.T) {

	t.Run("it returns the league table as JSON", func(t *testing.T) {
		wantedLeague := []Player{
			{"Cleo", 32},
			{"Chris", 20},
			{"Tiest", 14},
		}

		store := StubPlayerStore{nil, nil, wantedLeague}
		server := NewPlayerServer(&store)

		request, _ := http.NewRequest(http.MethodGet, "/league", nil)
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		var got []Player

		err := json.NewDecoder(response.Body).Decode(&got)

		if err != nil {
			t.Fatalf("Unable to parse response from server %q into slice of Player, '%v'", response.Body, err)
		}

		assertStatus(t, response.Code, http.StatusOK)

		if !reflect.DeepEqual(got, wantedLeague) {
			t.Errorf("got %v want %v", got, wantedLeague)
		}
	})
}
```

## حاول تشغيل الاختبار

```
./server_test.go:33:3: too few values in struct initializer
./server_test.go:70:3: too few values in struct initializer
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

ستحتاج إلى تحديث الاختبارات الأخرى لأن لدينا حقلاً جديداً في `StubPlayerStore`؛ اضبطه على `nil` في الاختبارات الأخرى.

حاول تشغيل الاختبارات مجدداً، وينبغي أن تحصل على

```
=== RUN   TestLeague/it_returns_the_league_table_as_JSON
    --- FAIL: TestLeague/it_returns_the_league_table_as_JSON (0.00s)
        server_test.go:124: got [{Chris 20}] want [{Cleo 32} {Chris 20} {Tiest 14}]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

نعرف أن البيانات موجودة في `StubPlayerStore`، وقد جرّدنا ذلك خلف الواجهة (interface) `PlayerStore`. ونحتاج إلى تحديثها كي يستطيع أي شخص يمرر إلينا `PlayerStore` أن يوفر لنا بيانات الدوريات.

```go
//server.go
type PlayerStore interface {
	GetPlayerScore(name string) int
	RecordWin(name string)
	GetLeague() []Player
}
```

يمكننا الآن تحديث شيفرة معالجنا لتستدعي ذلك بدلاً من إعادة قائمة ثابتة. احذف الطريقة (method) `getLeagueTable()` ثم حدّث `leagueHandler` لتستدعي `GetLeague()`.

```go
//server.go
func (p *PlayerServer) leagueHandler(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(p.store.GetLeague())
	w.WriteHeader(http.StatusOK)
}
```

حاول تشغيل الاختبارات.

```
# github.com/quii/learn-go-with-tests/json-and-io/v4
./main.go:9:50: cannot use NewInMemoryPlayerStore() (type *InMemoryPlayerStore) as type PlayerStore in argument to NewPlayerServer:
    *InMemoryPlayerStore does not implement PlayerStore (missing GetLeague method)
./server_integration_test.go:11:27: cannot use store (type *InMemoryPlayerStore) as type PlayerStore in argument to NewPlayerServer:
    *InMemoryPlayerStore does not implement PlayerStore (missing GetLeague method)
./server_test.go:36:28: cannot use &store (type *StubPlayerStore) as type PlayerStore in argument to NewPlayerServer:
    *StubPlayerStore does not implement PlayerStore (missing GetLeague method)
./server_test.go:74:28: cannot use &store (type *StubPlayerStore) as type PlayerStore in argument to NewPlayerServer:
    *StubPlayerStore does not implement PlayerStore (missing GetLeague method)
./server_test.go:106:29: cannot use &store (type *StubPlayerStore) as type PlayerStore in argument to NewPlayerServer:
    *StubPlayerStore does not implement PlayerStore (missing GetLeague method)
```

يعترض المصرِّف (compiler) لأن `InMemoryPlayerStore` و`StubPlayerStore` لا يملكان الطريقة الجديدة التي أضفناها إلى واجهتنا.

مع `StubPlayerStore` الأمر سهل جداً، فقط أعد الحقل `league` الذي أضفناه سابقاً.

```go
//server_test.go
func (s *StubPlayerStore) GetLeague() []Player {
	return s.league
}
```

إليك تذكيراً بكيفية تنفيذ `InMemoryStore`.

```go
//in_memory_player_store.go
type InMemoryPlayerStore struct {
	store map[string]int
}
```

مع أن تنفيذ `GetLeague` "كما ينبغي" بالمرور على الخريطة سيكون مباشراً جداً، تذكّر أننا نحاول فقط _كتابة أقل قدر من الشيفرة لجعل الاختبارات تنجح_.

لذا لنُرضِ المصرِّف الآن فحسب، ونتعايش مع الشعور غير المريح بوجود تنفيذ ناقص في `InMemoryStore`.

```go
//in_memory_player_store.go
func (i *InMemoryPlayerStore) GetLeague() []Player {
	return nil
}
```

ما يخبرنا به هذا حقاً أننا سنريد اختبار ذلك _لاحقاً_، لكن لنؤجله الآن.

حاول تشغيل الاختبارات، وينبغي أن ينجح التصريف وتنجح الاختبارات!

## أعد الهيكلة

شيفرة الاختبار لا تعبّر عن قصدنا جيداً، وفيها كثير من الشيفرة المتكررة التي يمكننا إزالتها بإعادة الهيكلة.

```go
//server_test.go
t.Run("it returns the league table as JSON", func(t *testing.T) {
	wantedLeague := []Player{
		{"Cleo", 32},
		{"Chris", 20},
		{"Tiest", 14},
	}

	store := StubPlayerStore{nil, nil, wantedLeague}
	server := NewPlayerServer(&store)

	request := newLeagueRequest()
	response := httptest.NewRecorder()

	server.ServeHTTP(response, request)

	got := getLeagueFromResponse(t, response.Body)
	assertStatus(t, response.Code, http.StatusOK)
	assertLeague(t, got, wantedLeague)
})
```

إليك الدوال المساعدة الجديدة

```go
//server_test.go
func getLeagueFromResponse(t testing.TB, body io.Reader) (league []Player) {
	t.Helper()
	err := json.NewDecoder(body).Decode(&league)

	if err != nil {
		t.Fatalf("Unable to parse response from server %q into slice of Player, '%v'", body, err)
	}

	return
}

func assertLeague(t testing.TB, got, want []Player) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Errorf("got %v want %v", got, want)
	}
}

func newLeagueRequest() *http.Request {
	req, _ := http.NewRequest(http.MethodGet, "/league", nil)
	return req
}
```

آخر ما علينا فعله ليعمل خادمنا هو التأكد من أننا نعيد ترويسة `content-type` في الاستجابة، كي تتعرف الآلات على أننا نعيد `JSON`.

## اكتب الاختبار أولاً

أضف هذا التوكيد إلى الاختبار الحالي

```go
//server_test.go
if response.Result().Header.Get("content-type") != "application/json" {
	t.Errorf("response did not have content-type of application/json, got %v", response.Result().Header)
}
```

## حاول تشغيل الاختبار

```
=== RUN   TestLeague/it_returns_the_league_table_as_JSON
    --- FAIL: TestLeague/it_returns_the_league_table_as_JSON (0.00s)
        server_test.go:124: response did not have content-type of application/json, got map[Content-Type:[text/plain; charset=utf-8]]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

حدّث `leagueHandler`

```go
//server.go
func (p *PlayerServer) leagueHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("content-type", "application/json")
	json.NewEncoder(w).Encode(p.store.GetLeague())
}
```

ينبغي أن ينجح الاختبار.

## أعد الهيكلة

أنشئ ثابتاً لـ"application/json" واستعمله في `leagueHandler`

```go
//server.go
const jsonContentType = "application/json"

func (p *PlayerServer) leagueHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("content-type", jsonContentType)
	json.NewEncoder(w).Encode(p.store.GetLeague())
}
```

ثم أضف دالة مساعدة `assertContentType`.

```go
//server_test.go
func assertContentType(t testing.TB, response *httptest.ResponseRecorder, want string) {
	t.Helper()
	if response.Result().Header.Get("content-type") != want {
		t.Errorf("response did not have content-type of %s, got %v", want, response.Result().Header)
	}
}
```

استعملها في الاختبار.

```go
//server_test.go
assertContentType(t, response, jsonContentType)
```

والآن بعد أن رتّبنا `PlayerServer` في الوقت الحالي، يمكننا تحويل انتباهنا إلى `InMemoryPlayerStore`، لأننا لو حاولنا الآن عرض هذا على مالكة المنتج فلن تعمل `/league`.

أسرع طريقة لنا للحصول على بعض الثقة هي الإضافة إلى اختبار التكامل، فنصل إلى نقطة النهاية الجديدة ونتحقق من أننا نحصل على الاستجابة الصحيحة من `/league`.

## اكتب الاختبار أولاً

يمكننا استعمال `t.Run` لتقسيم هذا الاختبار قليلاً، ويمكننا إعادة استعمال الدوال المساعدة من اختبارات الخادم، وهذا يبيّن مرة أخرى أهمية إعادة هيكلة الاختبارات.

```go
//server_integration_test.go
func TestRecordingWinsAndRetrievingThem(t *testing.T) {
	store := NewInMemoryPlayerStore()
	server := NewPlayerServer(store)
	player := "Pepper"

	server.ServeHTTP(httptest.NewRecorder(), newPostWinRequest(player))
	server.ServeHTTP(httptest.NewRecorder(), newPostWinRequest(player))
	server.ServeHTTP(httptest.NewRecorder(), newPostWinRequest(player))

	t.Run("get score", func(t *testing.T) {
		response := httptest.NewRecorder()
		server.ServeHTTP(response, newGetScoreRequest(player))
		assertStatus(t, response.Code, http.StatusOK)

		assertResponseBody(t, response.Body.String(), "3")
	})

	t.Run("get league", func(t *testing.T) {
		response := httptest.NewRecorder()
		server.ServeHTTP(response, newLeagueRequest())
		assertStatus(t, response.Code, http.StatusOK)

		got := getLeagueFromResponse(t, response.Body)
		want := []Player{
			{"Pepper", 3},
		}
		assertLeague(t, got, want)
	})
}
```

## حاول تشغيل الاختبار

```
=== RUN   TestRecordingWinsAndRetrievingThem/get_league
    --- FAIL: TestRecordingWinsAndRetrievingThem/get_league (0.00s)
        server_integration_test.go:35: got [] want [{Pepper 3}]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

يعيد `InMemoryPlayerStore` القيمة `nil` حين تستدعي `GetLeague()`، لذا سنحتاج إلى إصلاح ذلك.

```go
//in_memory_player_store.go
func (i *InMemoryPlayerStore) GetLeague() []Player {
	var league []Player
	for name, wins := range i.store {
		league = append(league, Player{name, wins})
	}
	return league
}
```

كل ما علينا فعله هو المرور على الخريطة وتحويل كل زوج مفتاح وقيمة إلى `Player`.

ينبغي أن ينجح الاختبار الآن.

## الخلاصة

واصلنا التقدم في برنامجنا بأمان باستعمال `TDD`، فجعلناه يدعم نقاط نهاية جديدة بطريقة قابلة للصيانة باستعمال موجِّه، وصار يستطيع الآن إعادة JSON لمستهلكينا. وفي الفصل التالي، سنتناول التخزين الدائم للبيانات وترتيب الدوري.

ما تناولناه:

- **التوجيه**. توفر لك المكتبة القياسية نوعاً سهل الاستعمال لإجراء التوجيه. وهو يتبنى بالكامل الواجهة `http.Handler`، إذ تسند المسارات إلى قيم `Handler`، والموجِّه نفسه أيضاً `Handler`. لكن ليست فيه بعض الميزات التي قد تتوقعها، مثل متغيرات المسار (كـ`/users/{id}`). ويمكنك بسهولة تحليل هذه المعلومات بنفسك، لكن قد ترغب في النظر في مكتبات توجيه أخرى إن صار ذلك عبئاً. ومعظم المكتبات الشائعة تلتزم بفلسفة المكتبة القياسية في تحقيق `http.Handler` أيضاً.
- **تضمين الأنواع**. تطرقنا قليلاً إلى هذا الأسلوب، لكن يمكنك [تعلّم المزيد عنه من Effective Go](https://golang.org/doc/effective_go.html#embedding). وإن كان هناك شيء واحد ينبغي أن تخرج به من هذا، فهو أنه قد يكون مفيداً للغاية، لكن _فكّر دائماً في واجهتك البرمجية العامة، ولا تكشف إلا ما هو مناسب_.
- **تحويل JSON من البيانات وإليها**. تجعل المكتبة القياسية تحويل بياناتك إلى صيغة متسلسلة وبالعكس أمراً بسيطاً جداً. كما أنها قابلة للضبط، ويمكنك تخصيص طريقة عمل تحويلات البيانات هذه إن لزم.
