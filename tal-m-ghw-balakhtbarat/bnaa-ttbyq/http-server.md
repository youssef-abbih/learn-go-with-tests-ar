# خادم HTTP

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/http-server)**

طُلب منك إنشاء خادم ويب يستطيع المستخدمون من خلاله تتبع عدد المباريات التي فاز بها اللاعبون.

-   ينبغي أن يعيد `GET /players/{name}` عدداً يمثل إجمالي عدد مرات الفوز
-   وينبغي أن يسجّل `POST /players/{name}` فوزاً لذلك الاسم، فيزيد العدد مع كل `POST` لاحق

سنتبع أسلوب `TDD`، فنحصل على برنامج يعمل بأسرع ما يمكن، ثم نجري تحسينات تكرارية صغيرة حتى نصل إلى الحل. وباتباع هذا الأسلوب فإننا

-   نُبقي فضاء المشكلة صغيراً في أي لحظة
-   لا نقع في المتاهات
-   إن علقنا أو تهنا يوماً، فلن يضيع كثير من العمل بالتراجع.

## الأحمر، الأخضر، إعادة الهيكلة

شددنا في هذا الكتاب كله على عملية `TDD`: اكتب اختباراً (test) وشاهده يفشل (الأحمر)، واكتب _أقل_ قدر من الشيفرة (code) لجعله يعمل (الأخضر)، ثم أعد الهيكلة.

هذا الانضباط في كتابة أقل قدر من الشيفرة مهم من حيث الأمان الذي يمنحك إياه `TDD`. فينبغي أن تسعى إلى الخروج من "الأحمر" بأسرع ما يمكن.

يصف كينت بيك ذلك هكذا:

> اجعل الاختبار يعمل بسرعة، مرتكباً ما يلزم من الخطايا في الطريق.

يمكنك ارتكاب هذه الخطايا لأنك ستعيد الهيكلة بعد ذلك مدعوماً بأمان الاختبارات.

### ماذا لو لم تفعل هذا؟

كلما أجريت تغييرات أكثر وأنت في الأحمر، زاد احتمال أن تضيف مشكلات أخرى لا تغطيها الاختبارات.

الفكرة أن تكتب شيفرة مفيدة تكرارياً بخطوات صغيرة، تقودها الاختبارات، كي لا تقع في متاهة لساعات.

### الدجاجة والبيضة

كيف نبني هذا تدريجياً؟ لا يمكننا جلب لاعب بـ`GET` دون أن نكون قد خزّنا شيئاً، ويبدو من الصعب معرفة ما إذا كان `POST` قد نجح دون وجود نقطة النهاية `GET` مسبقاً.

وهنا تتألق _المحاكاة_.

-   سيحتاج `GET` إلى _شيء_ من نوع `PlayerStore` للحصول على نتائج اللاعب. وينبغي أن يكون هذا واجهة (interface)، كي نستطيع عند الاختبار إنشاء بديل ثابت (stub) بسيط لاختبار شيفرتنا دون الحاجة إلى تنفيذ أي شيفرة تخزين فعلية.
-   ولـ`POST` يمكننا _التجسس_ على استدعاءاته لـ`PlayerStore` للتأكد من أنه يخزّن اللاعبين بشكل صحيح. ولن يقترن تنفيذنا للحفظ بالاسترجاع.
-   وللحصول على برنامج يعمل بسرعة، يمكننا صنع تنفيذ بسيط جداً في الذاكرة، ثم لاحقاً إنشاء تنفيذ مدعوم بأي آلية تخزين نفضّلها.

## اكتب الاختبار أولاً

يمكننا كتابة اختبار وجعله ينجح بإعادة قيمة ثابتة لنبدأ. ويسمي كينت بيك هذا "التزييف". وبمجرد أن يكون لدينا اختبار يعمل، يمكننا كتابة مزيد من الاختبارات لمساعدتنا على إزالة ذلك الثابت.

بهذه الخطوة الصغيرة جداً، يمكننا تحقيق البداية المهمة، وهي جعل البنية العامة للمشروع تعمل بشكل صحيح دون القلق كثيراً بشأن منطق تطبيقنا.

لإنشاء خادم ويب في غو (Go)، ستستدعي عادةً [ListenAndServe](https://golang.org/pkg/net/http/#ListenAndServe).

```go
func ListenAndServe(addr string, handler Handler) error
```

سيبدأ هذا خادم ويب يستمع على منفذ، وينشئ `goroutine` لكل طلب ويشغّله على [`Handler`](https://golang.org/pkg/net/http/#Handler).

```go
type Handler interface {
	ServeHTTP(ResponseWriter, *Request)
}
```

يحقق النوع (type) الواجهة `Handler` بتنفيذ الطريقة (method) `ServeHTTP` التي تتوقع وسيطين (arguments)، الأول هو المكان الذي _نكتب فيه استجابتنا_، والثاني هو طلب HTTP الذي أُرسل إلى الخادم.

لننشئ ملفاً باسم `server_test.go` ونكتب اختباراً لدالة (function) باسم `PlayerServer` تأخذ هذين الوسيطين. سيكون الطلب المرسل للحصول على نتيجة لاعب، ونتوقع أن تكون `"20"`.
```go
func TestGETPlayers(t *testing.T) {
	t.Run("returns Pepper's score", func(t *testing.T) {
		request, _ := http.NewRequest(http.MethodGet, "/players/Pepper", nil)
		response := httptest.NewRecorder()

		PlayerServer(response, request)

		got := response.Body.String()
		want := "20"

		if got != want {
			t.Errorf("got %q, want %q", got, want)
		}
	})
}
```

لاختبار خادمنا، سنحتاج إلى `Request` نرسله، وسنريد _التجسس_ على ما يكتبه معالجنا (handler) في `ResponseWriter`.

-   نستعمل `http.NewRequest` لإنشاء طلب. الوسيط الأول هو طريقة الطلب، والثاني هو مسار الطلب. أما الوسيط `nil` فيشير إلى متن الطلب، ولا نحتاج إلى ضبطه في هذه الحالة.
-   في الحزمة `net/http/httptest` جاسوس جاهز لنا اسمه `ResponseRecorder` يمكننا استعماله. وفيه كثير من الطرق المفيدة لفحص ما كُتب كاستجابة.

## حاول تشغيل الاختبار

`./server_test.go:13:2: undefined: PlayerServer`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

المصرِّف (compiler) هنا ليساعدك، فأصغِ إليه فحسب.

أنشئ ملفاً باسم `server.go` وعرّف `PlayerServer`

```go
func PlayerServer() {}
```

حاول مجدداً

```
./server_test.go:13:14: too many arguments in call to PlayerServer
    have (*httptest.ResponseRecorder, *http.Request)
    want ()
```

أضف الوسطاء إلى دالتنا

```go
import "net/http"

func PlayerServer(w http.ResponseWriter, r *http.Request) {

}
```

صارت الشيفرة تُصرَّف الآن والاختبار يفشل

```
=== RUN   TestGETPlayers/returns_Pepper's_score
    --- FAIL: TestGETPlayers/returns_Pepper's_score (0.00s)
        server_test.go:20: got '', want '20'
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

في فصل حقن التبعية، تطرقنا إلى خوادم HTTP مع الدالة `Greet`. وتعلّمنا أن `ResponseWriter` في `net/http` يحقق أيضاً `Writer` من `io`، لذا يمكننا استعمال `fmt.Fprint` لإرسال السلاسل النصية في استجابات HTTP التي نعيدها.

```go
func PlayerServer(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, "20")
}
```

ينبغي أن ينجح الاختبار الآن.

## أكمل الهيكل المبدئي

نريد ربط هذا في تطبيق. وهذا مهم لأن

-   سيكون لدينا _برنامج يعمل فعلاً_، فنحن لا نريد كتابة الاختبارات لمجرد كتابتها، ومن الجيد أن نرى الشيفرة تعمل.
-   ومع إعادة هيكلة شيفرتنا، يُرجَّح أن نغيّر بنية البرنامج. ونريد التأكد من أن ذلك ينعكس في تطبيقنا أيضاً كجزء من الأسلوب التدريجي.

أنشئ ملفاً جديداً `main.go` لتطبيقنا وضع فيه هذه الشيفرة

```go
package main

import (
	"log"
	"net/http"
)

func main() {
	handler := http.HandlerFunc(PlayerServer)
	log.Fatal(http.ListenAndServe(":5000", handler))
}
```

حتى الآن كانت كل شيفرة تطبيقنا في ملف واحد، لكن هذه ليست أفضل ممارسة في المشاريع الأكبر حيث ستريد فصل الأشياء في ملفات مختلفة.

لتشغيل هذا، نفّذ `go build`، الذي سيأخذ كل ملفات `.go` في المجلد ويبني لك برنامجاً. ثم يمكنك تنفيذه بـ`./myprogram`.

### النوع `http.HandlerFunc`

رأينا سابقاً أن الواجهة `Handler` هي ما نحتاج إلى تحقيقه لصنع خادم. و_عادةً_ نفعل ذلك بإنشاء `struct` وجعلها تحقق الواجهة بتنفيذ طريقة `ServeHTTP` خاصة بها. لكن البنى تُستعمل للاحتفاظ بالبيانات، وليست لدينا حالة _حالياً_، لذا لا يبدو إنشاء واحدة صائباً.

يتيح لنا [HandlerFunc](https://golang.org/pkg/net/http/#HandlerFunc) تجنب ذلك.

> النوع `HandlerFunc` محوّل يتيح استعمال الدوال العادية كمعالجات HTTP. فإن كانت `f` دالة لها التوقيع المناسب، فإن `HandlerFunc(f)` معالج `Handler` يستدعي `f`.

```go
type HandlerFunc func(ResponseWriter, *Request)
```

نرى من التوثيق أن النوع `HandlerFunc` قد نفّذ بالفعل الطريقة `ServeHTTP`.
وبتحويل نوع دالتنا `PlayerServer` إليه، نكون قد حققنا `Handler` المطلوب.

### الدالة `http.ListenAndServe(":5000"...)`

تأخذ `ListenAndServe` منفذاً للاستماع عليه و`Handler`. وإن كانت هناك مشكلة، فسيعيد خادم الويب خطأً (error)، ومثال ذلك أن يكون المنفذ مستعملاً بالفعل. ولهذا السبب نغلّف الاستدعاء في `log.Fatal` لتسجيل الخطأ للمستخدم.

ما سنفعله الآن هو كتابة اختبار _آخر_ يجبرنا على إجراء تغيير إيجابي لمحاولة الابتعاد عن القيمة الثابتة.

## اكتب الاختبار أولاً

سنضيف اختباراً فرعياً (subtest) آخر إلى مجموعتنا يحاول الحصول على نتيجة لاعب مختلف، وهذا سيكسر أسلوب القيمة الثابتة.

```go
t.Run("returns Floyd's score", func(t *testing.T) {
	request, _ := http.NewRequest(http.MethodGet, "/players/Floyd", nil)
	response := httptest.NewRecorder()

	PlayerServer(response, request)

	got := response.Body.String()
	want := "10"

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
})
```

لعلك كنت تفكر

> بالتأكيد نحتاج إلى نوع من مفهوم التخزين للتحكم بأي لاعب يحصل على أي نتيجة. من الغريب أن القيم تبدو اعتباطية إلى هذا الحد في اختباراتنا.

تذكّر أننا نحاول فقط اتخاذ أصغر الخطوات الممكنة بشكل معقول، لذا نحاول الآن فقط كسر الثابت.

## حاول تشغيل الاختبار

```
=== RUN   TestGETPlayers/returns_Pepper's_score
    --- PASS: TestGETPlayers/returns_Pepper's_score (0.00s)
=== RUN   TestGETPlayers/returns_Floyd's_score
    --- FAIL: TestGETPlayers/returns_Floyd's_score (0.00s)
        server_test.go:34: got '20', want '10'
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
//server.go
func PlayerServer(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")

	if player == "Pepper" {
		fmt.Fprint(w, "20")
		return
	}

	if player == "Floyd" {
		fmt.Fprint(w, "10")
		return
	}
}
```

أجبرنا هذا الاختبار على النظر فعلاً في عنوان URL للطلب واتخاذ قرار. لذا فبينما ربما كنا نقلق في أذهاننا بشأن مخازن اللاعبين والواجهات، يبدو أن الخطوة المنطقية التالية تتعلق في الحقيقة بـ_التوجيه_.

لو بدأنا بشيفرة المخزن لكان قدر التغييرات التي علينا إجراؤها كبيراً جداً مقارنة بهذا. **فهذه خطوة أصغر نحو هدفنا النهائي، وقد قادتها الاختبارات**.

نقاوم الآن إغراء استعمال أي مكتبات توجيه، ونكتفي بأصغر خطوة لجعل اختبارنا ينجح.

تعيد `r.URL.Path` مسار الطلب، ويمكننا بعد ذلك استعمال [`strings.TrimPrefix`](https://golang.org/pkg/strings/#TrimPrefix) لاقتطاع `/players/` والحصول على اللاعب المطلوب. ليس هذا متيناً جداً، لكنه سيفي بالغرض حالياً.

## أعد الهيكلة

يمكننا تبسيط `PlayerServer` بفصل استرجاع النتيجة في دالة

```go
//server.go
func PlayerServer(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")

	fmt.Fprint(w, GetPlayerScore(player))
}

func GetPlayerScore(name string) string {
	if name == "Pepper" {
		return "20"
	}

	if name == "Floyd" {
		return "10"
	}

	return ""
}
```

ويمكننا إزالة بعض التكرار في شيفرة الاختبارات بإنشاء بعض الدوال المساعدة

```go
//server_test.go
func TestGETPlayers(t *testing.T) {
	t.Run("returns Pepper's score", func(t *testing.T) {
		request := newGetScoreRequest("Pepper")
		response := httptest.NewRecorder()

		PlayerServer(response, request)

		assertResponseBody(t, response.Body.String(), "20")
	})

	t.Run("returns Floyd's score", func(t *testing.T) {
		request := newGetScoreRequest("Floyd")
		response := httptest.NewRecorder()

		PlayerServer(response, request)

		assertResponseBody(t, response.Body.String(), "10")
	})
}

func newGetScoreRequest(name string) *http.Request {
	req, _ := http.NewRequest(http.MethodGet, fmt.Sprintf("/players/%s", name), nil)
	return req
}

func assertResponseBody(t testing.TB, got, want string) {
	t.Helper()
	if got != want {
		t.Errorf("response body is wrong, got %q want %q", got, want)
	}
}
```

لكن لا ينبغي أن نكون راضين بعد. فلا يبدو صائباً أن يعرف خادمنا النتائج.

أوضحت إعادة الهيكلة التي أجريناها ما علينا فعله.

نقلنا حساب النتيجة من الجسم الرئيسي لمعالجنا إلى دالة `GetPlayerScore`. ويبدو هذا المكان الصحيح لفصل الاهتمامات باستعمال الواجهات.

لننقل الدالة التي أعدنا هيكلتها لتصبح واجهة بدلاً من ذلك

```go
type PlayerStore interface {
	GetPlayerScore(name string) int
}
```

لكي يستطيع `PlayerServer` استعمال `PlayerStore`، سيحتاج إلى مرجع إليه. ويبدو الآن الوقت المناسب لتغيير معماريتنا بحيث يصبح `PlayerServer` بنية `struct`.

```go
type PlayerServer struct {
	store PlayerStore
}
```

وأخيراً، سنحقق الآن الواجهة `Handler` بإضافة طريقة إلى بنيتنا الجديدة ووضع شيفرة معالجنا الحالية فيها.

```go
func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")
	fmt.Fprint(w, p.store.GetPlayerScore(player))
}
```

التغيير الآخر الوحيد أننا صرنا نستدعي `store.GetPlayerScore` للحصول على النتيجة، بدلاً من الدالة المحلية التي عرّفناها (والتي يمكننا حذفها الآن).

إليك الشيفرة الكاملة لخادمنا

```go
//server.go
type PlayerStore interface {
	GetPlayerScore(name string) int
}

type PlayerServer struct {
	store PlayerStore
}

func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")
	fmt.Fprint(w, p.store.GetPlayerScore(player))
}
```

### أصلح المشكلات

كانت هذه تغييرات كثيرة إلى حد ما، ونعرف أن اختباراتنا وتطبيقنا لن تُصرَّف بعد الآن، لكن استرخِ ودع المصرِّف يرشدك خلالها.

`./main.go:9:58: type PlayerServer is not an expression`

علينا تغيير اختباراتنا لتنشئ بدلاً من ذلك نسخة جديدة من `PlayerServer` ثم تستدعي طريقتها `ServeHTTP`.

```go
//server_test.go
func TestGETPlayers(t *testing.T) {
	server := &PlayerServer{}

	t.Run("returns Pepper's score", func(t *testing.T) {
		request := newGetScoreRequest("Pepper")
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertResponseBody(t, response.Body.String(), "20")
	})

	t.Run("returns Floyd's score", func(t *testing.T) {
		request := newGetScoreRequest("Floyd")
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertResponseBody(t, response.Body.String(), "10")
	})
}
```

لاحظ أننا ما زلنا لا نقلق بشأن صنع المخازن _بعد_، فنحن نريد فقط أن ينجح التصريف بأسرع ما يمكن.

ينبغي أن تعتاد على إعطاء الأولوية لوجود شيفرة تُصرَّف، ثم لشيفرة تنجح في الاختبارات.

فبإضافة مزيد من الوظائف (مثل المخازن الثابتة) بينما الشيفرة لا تُصرَّف، فإننا نعرّض أنفسنا لمشكلات تصريف محتملة _أكثر_.

والآن لن يُصرَّف `main.go` للسبب نفسه.

```go
func main() {
	server := &PlayerServer{}
	log.Fatal(http.ListenAndServe(":5000", server))
}
```

أخيراً، كل شيء يُصرَّف لكن الاختبارات تفشل

```
=== RUN   TestGETPlayers/returns_the_Pepper's_score
panic: runtime error: invalid memory address or nil pointer dereference [recovered]
    panic: runtime error: invalid memory address or nil pointer dereference
```

وذلك لأننا لم نمرر `PlayerStore` في اختباراتنا. سنحتاج إلى صنع بديل ثابت منه.

```go
//server_test.go
type StubPlayerStore struct {
	scores map[string]int
}

func (s *StubPlayerStore) GetPlayerScore(name string) int {
	score := s.scores[name]
	return score
}
```

الخريطة `map` وسيلة سريعة وسهلة لصنع مخزن ثابت من المفاتيح والقيم لاختباراتنا. لننشئ الآن واحداً من هذه المخازن لاختباراتنا ونمرره إلى `PlayerServer`.

```go
//server_test.go
func TestGETPlayers(t *testing.T) {
	store := StubPlayerStore{
		map[string]int{
			"Pepper": 20,
			"Floyd":  10,
		},
	}
	server := &PlayerServer{&store}

	t.Run("returns Pepper's score", func(t *testing.T) {
		request := newGetScoreRequest("Pepper")
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertResponseBody(t, response.Body.String(), "20")
	})

	t.Run("returns Floyd's score", func(t *testing.T) {
		request := newGetScoreRequest("Floyd")
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertResponseBody(t, response.Body.String(), "10")
	})
}
```

تنجح اختباراتنا الآن وتبدو أفضل. وصار _القصد_ من شيفرتنا أوضح الآن بفضل تقديم المخزن. فنحن نخبر القارئ أنه لأن لدينا _هذه البيانات في `PlayerStore`_، فحين تستعمله مع `PlayerServer` ينبغي أن تحصل على الاستجابات التالية.

### شغّل التطبيق

والآن بعد أن نجحت اختباراتنا، آخر ما علينا فعله لإتمام إعادة الهيكلة هذه هو التحقق من أن تطبيقنا يعمل. ينبغي أن يبدأ البرنامج، لكنك ستحصل على استجابة فظيعة إن حاولت الوصول إلى الخادم على `http://localhost:5000/players/Pepper`.

والسبب أننا لم نمرر `PlayerStore`.

سنحتاج إلى صنع تنفيذ له، لكن هذا صعب الآن لأننا لا نخزّن أي بيانات ذات معنى، لذا سيكون ثابتاً في الوقت الحالي.

```go
//main.go
type InMemoryPlayerStore struct{}

func (i *InMemoryPlayerStore) GetPlayerScore(name string) int {
	return 123
}

func main() {
	server := &PlayerServer{&InMemoryPlayerStore{}}
	log.Fatal(http.ListenAndServe(":5000", server))
}
```

إن شغّلت `go build` مجدداً ووصلت إلى عنوان URL نفسه، فينبغي أن تحصل على `"123"`. ليس رائعاً، لكنه أفضل ما يمكننا فعله حتى نخزّن البيانات.
كما أنه لم يكن شعوراً جيداً أن يبدأ تطبيقنا الرئيسي دون أن يعمل فعلاً. فقد اضطررنا إلى الاختبار يدوياً لرؤية المشكلة.

لدينا بعض الخيارات لما نفعله بعد ذلك

-   معالجة سيناريو عدم وجود اللاعب
-   معالجة سيناريو `POST /players/{name}`

مع أن سيناريو `POST` يقربنا من "المسار الناجح"، أشعر أن معالجة سيناريو اللاعب المفقود أولاً ستكون أسهل لأننا في ذلك السياق بالفعل. وسنصل إلى البقية لاحقاً.

## اكتب الاختبار أولاً

أضف سيناريو اللاعب المفقود إلى مجموعتنا الحالية

```go
//server_test.go
t.Run("returns 404 on missing players", func(t *testing.T) {
	request := newGetScoreRequest("Apollo")
	response := httptest.NewRecorder()

	server.ServeHTTP(response, request)

	got := response.Code
	want := http.StatusNotFound

	if got != want {
		t.Errorf("got status %d want %d", got, want)
	}
})
```

## حاول تشغيل الاختبار

```
=== RUN   TestGETPlayers/returns_404_on_missing_players
    --- FAIL: TestGETPlayers/returns_404_on_missing_players (0.00s)
        server_test.go:56: got status 200 want 404
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
//server.go
func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")

	w.WriteHeader(http.StatusNotFound)

	fmt.Fprint(w, p.store.GetPlayerScore(player))
}
```

أحياناً أتبرم كثيراً حين يقول دعاة `TDD` "تأكد من أنك تكتب فقط أقل قدر من الشيفرة لجعله ينجح"، لأن ذلك قد يبدو تحذلقاً.

لكن هذا السيناريو يوضح المثال جيداً. فقد فعلت الحد الأدنى المطلق (مع علمي بأنه غير صحيح)، وهو كتابة `StatusNotFound` في **كل الاستجابات**، ومع ذلك تنجح كل اختباراتنا!

**بفعل الحد الأدنى المطلق لجعل الاختبارات تنجح، يمكن أن تنكشف الثغرات في اختباراتك**. ففي حالتنا، لا نؤكد أننا ينبغي أن نحصل على `StatusOK` حين يكون اللاعبون موجودين _فعلاً_ في المخزن.

حدّث الاختبارين الآخرين ليؤكدا على الحالة، وأصلح الشيفرة.

إليك الاختبارات الجديدة

```go
//server_test.go
func TestGETPlayers(t *testing.T) {
	store := StubPlayerStore{
		map[string]int{
			"Pepper": 20,
			"Floyd":  10,
		},
	}
	server := &PlayerServer{&store}

	t.Run("returns Pepper's score", func(t *testing.T) {
		request := newGetScoreRequest("Pepper")
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertStatus(t, response.Code, http.StatusOK)
		assertResponseBody(t, response.Body.String(), "20")
	})

	t.Run("returns Floyd's score", func(t *testing.T) {
		request := newGetScoreRequest("Floyd")
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertStatus(t, response.Code, http.StatusOK)
		assertResponseBody(t, response.Body.String(), "10")
	})

	t.Run("returns 404 on missing players", func(t *testing.T) {
		request := newGetScoreRequest("Apollo")
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertStatus(t, response.Code, http.StatusNotFound)
	})
}

func assertStatus(t testing.TB, got, want int) {
	t.Helper()
	if got != want {
		t.Errorf("did not get correct status, got %d, want %d", got, want)
	}
}

func newGetScoreRequest(name string) *http.Request {
	req, _ := http.NewRequest(http.MethodGet, fmt.Sprintf("/players/%s", name), nil)
	return req
}

func assertResponseBody(t testing.TB, got, want string) {
	t.Helper()
	if got != want {
		t.Errorf("response body is wrong, got %q want %q", got, want)
	}
}
```

صرنا نتحقق من الحالة في كل اختباراتنا، لذا أنشأت دالة مساعدة `assertStatus` لتسهيل ذلك.

والآن يفشل اختبارانا الأولان بسبب 404 بدلاً من 200، لذا يمكننا إصلاح `PlayerServer` ليعيد "غير موجود" فقط إن كانت النتيجة 0.

```go
//server.go
func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")

	score := p.store.GetPlayerScore(player)

	if score == 0 {
		w.WriteHeader(http.StatusNotFound)
	}

	fmt.Fprint(w, score)
}
```

### تخزين النتائج

والآن بعد أن صرنا نستطيع استرجاع النتائج من مخزن، صار من المنطقي أن نستطيع تخزين نتائج جديدة.

## اكتب الاختبار أولاً

```go
//server_test.go
func TestStoreWins(t *testing.T) {
	store := StubPlayerStore{
		map[string]int{},
	}
	server := &PlayerServer{&store}

	t.Run("it returns accepted on POST", func(t *testing.T) {
		request, _ := http.NewRequest(http.MethodPost, "/players/Pepper", nil)
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertStatus(t, response.Code, http.StatusAccepted)
	})
}
```

في البداية لنتحقق فقط من أننا نحصل على رمز الحالة الصحيح إن وصلنا إلى المسار المعيّن بطلب POST. وهذا يتيح لنا استخلاص وظيفة قبول نوع مختلف من الطلبات ومعالجته بشكل مختلف عن `GET /players/{name}`. وبمجرد أن يعمل هذا، يمكننا البدء بالتوكيد على تفاعل معالجنا مع المخزن.

## حاول تشغيل الاختبار

```
=== RUN   TestStoreWins/it_returns_accepted_on_POST
    --- FAIL: TestStoreWins/it_returns_accepted_on_POST (0.00s)
        server_test.go:70: did not get correct status, got 404, want 202
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

تذكّر أننا نرتكب الخطايا عمداً، لذا ستفي تعليمة `if` مبنية على طريقة الطلب بالغرض.

```go
//server.go
func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {

	if r.Method == http.MethodPost {
		w.WriteHeader(http.StatusAccepted)
		return
	}

	player := strings.TrimPrefix(r.URL.Path, "/players/")

	score := p.store.GetPlayerScore(player)

	if score == 0 {
		w.WriteHeader(http.StatusNotFound)
	}

	fmt.Fprint(w, score)
}
```

## أعد الهيكلة

يبدو المعالج مشوشاً بعض الشيء الآن. لنقسّم الشيفرة لنجعلها أسهل متابعة، ونعزل الوظائف المختلفة في دوال جديدة.

```go
//server.go
func (p *PlayerServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {

	switch r.Method {
	case http.MethodPost:
		p.processWin(w)
	case http.MethodGet:
		p.showScore(w, r)
	}

}

func (p *PlayerServer) showScore(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")

	score := p.store.GetPlayerScore(player)

	if score == 0 {
		w.WriteHeader(http.StatusNotFound)
	}

	fmt.Fprint(w, score)
}

func (p *PlayerServer) processWin(w http.ResponseWriter) {
	w.WriteHeader(http.StatusAccepted)
}
```

وهذا يجعل جانب التوجيه في `ServeHTTP` أوضح قليلاً، ويعني أن تكراراتنا التالية في التخزين يمكن أن تكون داخل `processWin` فقط.

بعد ذلك، نريد التحقق من أنه حين ننفّذ `POST /players/{name}` يُطلب من `PlayerStore` تسجيل الفوز.

## اكتب الاختبار أولاً

يمكننا تحقيق ذلك بتوسيع `StubPlayerStore` بطريقة جديدة `RecordWin` ثم التجسس على استدعاءاتها.

```go
//server_test.go
type StubPlayerStore struct {
	scores   map[string]int
	winCalls []string
}

func (s *StubPlayerStore) GetPlayerScore(name string) int {
	score := s.scores[name]
	return score
}

func (s *StubPlayerStore) RecordWin(name string) {
	s.winCalls = append(s.winCalls, name)
}
```

والآن وسّع اختبارنا للتحقق من عدد الاستدعاءات في البداية

```go
//server_test.go
func TestStoreWins(t *testing.T) {
	store := StubPlayerStore{
		map[string]int{},
	}
	server := &PlayerServer{&store}

	t.Run("it records wins when POST", func(t *testing.T) {
		request := newPostWinRequest("Pepper")
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertStatus(t, response.Code, http.StatusAccepted)

		if len(store.winCalls) != 1 {
			t.Errorf("got %d calls to RecordWin want %d", len(store.winCalls), 1)
		}
	})
}

func newPostWinRequest(name string) *http.Request {
	req, _ := http.NewRequest(http.MethodPost, fmt.Sprintf("/players/%s", name), nil)
	return req
}
```

## حاول تشغيل الاختبار

```
./server_test.go:26:20: too few values in struct initializer
./server_test.go:65:20: too few values in struct initializer
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

علينا تحديث شيفرتنا في المواضع التي ننشئ فيها `StubPlayerStore` لأننا أضفنا حقلاً جديداً

```go
//server_test.go
store := StubPlayerStore{
	map[string]int{},
	nil,
}
```

```
--- FAIL: TestStoreWins (0.00s)
    --- FAIL: TestStoreWins/it_records_wins_when_POST (0.00s)
        server_test.go:80: got 0 calls to RecordWin want 1
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

بما أننا نؤكد فقط عدد الاستدعاءات لا القيم المحددة، فإن ذلك يجعل تكرارنا الأول أصغر قليلاً.

علينا تحديث تصور `PlayerServer` لما هو `PlayerStore` بتغيير الواجهة، إن أردنا أن نستطيع استدعاء `RecordWin`.

```go
//server.go
type PlayerStore interface {
	GetPlayerScore(name string) int
	RecordWin(name string)
}
```

وبفعل هذا لم يعد `main` يُصرَّف

```
./main.go:17:46: cannot use InMemoryPlayerStore literal (type *InMemoryPlayerStore) as type PlayerStore in field value:
    *InMemoryPlayerStore does not implement PlayerStore (missing RecordWin method)
```

يخبرنا المصرِّف بما هو خاطئ. لنحدّث `InMemoryPlayerStore` لتكون لديه تلك الطريقة.

```go
//main.go
type InMemoryPlayerStore struct{}

func (i *InMemoryPlayerStore) RecordWin(name string) {}
```

حاول تشغيل الاختبارات، وينبغي أن نعود إلى شيفرة تُصرَّف، لكن الاختبار ما زال يفشل.

والآن بعد أن صارت لدى `PlayerStore` الطريقة `RecordWin`، يمكننا استدعاؤها داخل `PlayerServer`

```go
//server.go
func (p *PlayerServer) processWin(w http.ResponseWriter) {
	p.store.RecordWin("Bob")
	w.WriteHeader(http.StatusAccepted)
}
```

شغّل الاختبارات وينبغي أن تنجح! من الواضح أن `"Bob"` ليس بالضبط ما نريد إرساله إلى `RecordWin`، فلنحسّن الاختبار أكثر.

## اكتب الاختبار أولاً

```go
//server_test.go
func TestStoreWins(t *testing.T) {
	store := StubPlayerStore{
		map[string]int{},
		nil,
	}
	server := &PlayerServer{&store}

	t.Run("it records wins on POST", func(t *testing.T) {
		player := "Pepper"

		request := newPostWinRequest(player)
		response := httptest.NewRecorder()

		server.ServeHTTP(response, request)

		assertStatus(t, response.Code, http.StatusAccepted)

		if len(store.winCalls) != 1 {
			t.Fatalf("got %d calls to RecordWin want %d", len(store.winCalls), 1)
		}

		if store.winCalls[0] != player {
			t.Errorf("did not store correct winner got %q want %q", store.winCalls[0], player)
		}
	})
}
```

والآن بعد أن عرفنا أن في الشريحة `winCalls` عنصراً واحداً، يمكننا الإشارة بأمان إلى العنصر الأول والتحقق من أنه يساوي `player`.

## حاول تشغيل الاختبار

```
=== RUN   TestStoreWins/it_records_wins_on_POST
    --- FAIL: TestStoreWins/it_records_wins_on_POST (0.00s)
        server_test.go:86: did not store correct winner got 'Bob' want 'Pepper'
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
//server.go
func (p *PlayerServer) processWin(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")
	p.store.RecordWin(player)
	w.WriteHeader(http.StatusAccepted)
}
```

غيّرنا `processWin` لتأخذ `http.Request` كي نستطيع النظر في عنوان URL لاستخراج اسم اللاعب. وبمجرد أن نحصل عليه، يمكننا استدعاء `store` بالقيمة الصحيحة لجعل الاختبار ينجح.

## أعد الهيكلة

يمكننا إزالة بعض التكرار في هذه الشيفرة، لأننا نستخرج اسم اللاعب بالطريقة نفسها في مكانين

```go
//server.go
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

مع أن اختباراتنا تنجح، فليس لدينا حقاً برنامج يعمل. فإن حاولت تشغيل `main` واستعمال البرنامج كما هو مقصود، فلن يعمل لأننا لم نصل بعد إلى تنفيذ `PlayerStore` بشكل صحيح. لكن لا بأس بهذا؛ فبالتركيز على معالجنا حددنا الواجهة التي نحتاج إليها، بدلاً من محاولة تصميمها مسبقاً.

_يمكننا_ البدء بكتابة بعض الاختبارات حول `InMemoryPlayerStore`، لكنه موجود هنا مؤقتاً فقط حتى ننفّذ طريقة أكثر متانة لتخزين نتائج اللاعبين بشكل دائم (أي قاعدة بيانات).

ما سنفعله الآن هو كتابة _اختبار تكامل_ بين `PlayerServer` و`InMemoryPlayerStore` لإتمام الوظيفة. وهذا سيتيح لنا الوصول إلى هدفنا، وهو الثقة بأن تطبيقنا يعمل، دون الحاجة إلى اختبار `InMemoryPlayerStore` مباشرة. وليس ذلك فحسب، بل حين نصل إلى تنفيذ `PlayerStore` بقاعدة بيانات، يمكننا اختبار ذلك التنفيذ باختبار التكامل نفسه.

### اختبارات التكامل

قد تكون اختبارات التكامل (integration tests) مفيدة لاختبار أن مناطق أكبر من نظامك تعمل، لكن عليك أن تتذكر أنها:

-   أصعب في الكتابة
-   حين تفشل، قد يكون من الصعب معرفة السبب (عادةً يكون خطأً برمجياً داخل أحد مكونات اختبار التكامل)، لذا قد يكون إصلاحها أصعب
-   أبطأ تشغيلاً أحياناً (لأنها كثيراً ما تُستعمل مع مكونات "حقيقية" مثل قاعدة بيانات)

لهذا السبب، يُنصح بأن تبحث في موضوع _هرم الاختبارات_.

## اكتب الاختبار أولاً

اختصاراً، سأعرض عليك اختبار التكامل النهائي بعد إعادة هيكلته.

```go
// server_integration_test.go
package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRecordingWinsAndRetrievingThem(t *testing.T) {
	store := InMemoryPlayerStore{}
	server := PlayerServer{&store}
	player := "Pepper"

	server.ServeHTTP(httptest.NewRecorder(), newPostWinRequest(player))
	server.ServeHTTP(httptest.NewRecorder(), newPostWinRequest(player))
	server.ServeHTTP(httptest.NewRecorder(), newPostWinRequest(player))

	response := httptest.NewRecorder()
	server.ServeHTTP(response, newGetScoreRequest(player))
	assertStatus(t, response.Code, http.StatusOK)

	assertResponseBody(t, response.Body.String(), "3")
}
```

-   ننشئ المكونين اللذين نحاول تكاملهما: `InMemoryPlayerStore` و`PlayerServer`.
-   ثم نرسل 3 طلبات لتسجيل 3 مرات فوز لـ`player`. ولا نهتم كثيراً برموز الحالة في هذا الاختبار، لأنها لا تتعلق بمدى تكاملهما جيداً.
-   أما الاستجابة التالية فنهتم بها (لذا نخزّنها في متغير `response`)، لأننا سنحاول الحصول على نتيجة `player`.

## حاول تشغيل الاختبار

```
--- FAIL: TestRecordingWinsAndRetrievingThem (0.00s)
    server_integration_test.go:24: response body is wrong, got '123' want '3'
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

سآخذ هنا بعض الحرية وأكتب شيفرة أكثر مما قد ترتاح إليه دون كتابة اختبار.

_هذا مسموح!_ فما زال لدينا اختبار يتحقق من أن الأشياء ينبغي أن تعمل بشكل صحيح، لكنه ليس حول الوحدة المحددة التي نعمل عليها (`InMemoryPlayerStore`).

لو علقت في هذا السيناريو، لتراجعت عن تغييراتي إلى الاختبار الفاشل، ثم كتبت اختبارات وحدة أكثر تحديداً حول `InMemoryPlayerStore` لتساعدني على استخلاص حل.

```go
//in_memory_player_store.go
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

-   نحتاج إلى تخزين البيانات، لذا أضفت `map[string]int` إلى البنية `InMemoryPlayerStore`
-   وللتيسير أنشأت `NewInMemoryPlayerStore` لتهيئة المخزن، وحدّثت اختبار التكامل ليستعملها:
    ```go
    //server_integration_test.go
    store := NewInMemoryPlayerStore()
    server := PlayerServer{store}
    ```
-   وبقية الشيفرة ليست إلا تغليفاً حول `map`

ينجح اختبار التكامل، والآن علينا فقط تغيير `main` ليستعمل `NewInMemoryPlayerStore()`

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

ابنِه، وشغّله، ثم استعمل `curl` لاختباره.

-   شغّل هذا بضع مرات، وغيّر أسماء اللاعبين إن أحببت: `curl -X POST http://localhost:5000/players/Pepper`
-   تحقق من النتائج بـ`curl http://localhost:5000/players/Pepper`

رائع! لقد صنعت خدمة أشبه بـREST. وللمضي قدماً، ستريد اختيار مخزن بيانات لحفظ النتائج مدة أطول من مدة تشغيل البرنامج.

-   اختر مخزناً (Bolt؟ Mongo؟ Postgres؟ نظام الملفات؟)
-   اجعل `PostgresPlayerStore` يحقق `PlayerStore`
-   ابنِ الوظيفة بـ`TDD` كي تتأكد من أنها تعمل
-   وصّلها باختبار التكامل، وتحقق من أنه ما زال سليماً
-   وأخيراً وصّلها بـ`main`

## أعد الهيكلة

كدنا ننتهي! لنبذل بعض الجهد لمنع أخطاء التزامن مثل هذه

```
fatal error: concurrent map read and map write
```

بإضافة الأقفال نفرض أمان التزامن، خصوصاً للعدّاد في الدالة `RecordWin`. اقرأ المزيد عن الأقفال في فصل الحزمة `sync`.

## الخلاصة

### الواجهة `http.Handler`

-   حقق هذه الواجهة لإنشاء خوادم الويب
-   استعمل `http.HandlerFunc` لتحويل الدوال العادية إلى قيم `http.Handler`
-   استعمل `httptest.NewRecorder` لتمريره كـ`ResponseWriter` يتيح لك التجسس على الاستجابات التي يرسلها معالجك
-   استعمل `http.NewRequest` لبناء الطلبات التي تتوقع أن تصل إلى نظامك

### الواجهات والمحاكاة وحقن التبعية

-   تتيح لك بناء النظام تكرارياً على أجزاء أصغر
-   تتيح لك تطوير معالج يحتاج إلى تخزين دون الحاجة إلى تخزين فعلي
-   استعمل `TDD` لاستخلاص الواجهات التي تحتاج إليها

### ارتكب الخطايا، ثم أعد الهيكلة (ثم أودع في نظام التحكم بالمصدر)

-   عليك أن تعامل فشل التصريف أو فشل الاختبارات كحالة حمراء عليك الخروج منها بأسرع ما يمكن.
-   اكتب فقط الشيفرة اللازمة للوصول إلى ذلك. _ثم_ أعد الهيكلة واجعل الشيفرة جميلة.
-   محاولة إجراء تغييرات كثيرة جداً بينما الشيفرة لا تُصرَّف أو الاختبارات تفشل تعرّضك لخطر تفاقم المشكلات.
-   الالتزام بهذا الأسلوب يجبرك على كتابة اختبارات صغيرة، أي تغييرات صغيرة، وهذا يساعد على إبقاء العمل على الأنظمة المعقدة قابلاً للإدارة.
