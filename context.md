# الحزمة `context`

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/context)**

كثيراً ما تُطلق البرمجيات عمليات طويلة الأمد تستهلك موارد كثيرة (غالباً في `goroutines`). وإن أُلغي الإجراء الذي تسبب في ذلك أو فشل لسبب ما، فعليك إيقاف هذه العمليات بطريقة متسقة في كامل تطبيقك.

وإن لم تُدِر ذلك، فقد يبدأ تطبيق غو (Go) السريع الذي تفخر به بالمعاناة من مشكلات أداء يصعب تنقيحها.

سنستعمل في هذا الفصل الحزمة (package) `context` لمساعدتنا على إدارة العمليات طويلة الأمد.

سنبدأ بمثال كلاسيكي لخادم ويب يُطلق، حين يصله طلب، عملية قد تطول لجلب بعض البيانات كي يعيدها في الاستجابة.

سنختبر سيناريو يلغي فيه المستخدم الطلب قبل أن تُسترجع البيانات، وسنتأكد من أن العملية تُبلَّغ بأن تتوقف.

أعددت بعض الشيفرة (code) للمسار الناجح كي نبدأ. إليك شيفرة الخادم.

```go
func Server(store Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, store.Fetch())
	}
}
```

تأخذ الدالة (function) `Server` قيمة `Store` وتعيد لنا `http.HandlerFunc`. والنوع `Store` معرّف هكذا:

```go
type Store interface {
	Fetch() string
}
```

تستدعي الدالة المعادة الطريقة (method) `Fetch` على `store` للحصول على البيانات، وتكتبها في الاستجابة.

ولدينا جاسوس (spy) مقابل للنوع `Store` نستعمله في الاختبار.

```go
type SpyStore struct {
	response string
}

func (s *SpyStore) Fetch() string {
	return s.response
}

func TestServer(t *testing.T) {
	data := "hello, world"
	svr := Server(&SpyStore{data})

	request := httptest.NewRequest(http.MethodGet, "/", nil)
	response := httptest.NewRecorder()

	svr.ServeHTTP(response, request)

	if response.Body.String() != data {
		t.Errorf(`got "%s", want "%s"`, response.Body.String(), data)
	}
}
```

والآن بعد أن صار لدينا مسار ناجح، نريد سيناريو أكثر واقعية لا تستطيع فيه `Store` إنهاء `Fetch` قبل أن يلغي المستخدم الطلب.

## اكتب الاختبار أولاً

سيحتاج معالجنا (handler) إلى وسيلة يطلب بها من `Store` إلغاء العمل، لذا حدّث الواجهة (interface).

```go
type Store interface {
	Fetch() string
	Cancel()
}
```

سنحتاج إلى تعديل جاسوسنا بحيث يستغرق بعض الوقت لإعادة `data`، وتكون لديه وسيلة لمعرفة أنه طُلب منه الإلغاء. وعليه أن يضيف `Cancel` كطريقة لتحقيق الواجهة `Store`.

```go
type SpyStore struct {
	response  string
	cancelled bool
}

func (s *SpyStore) Fetch() string {
	time.Sleep(100 * time.Millisecond)
	return s.response
}

func (s *SpyStore) Cancel() {
	s.cancelled = true
}
```

لنُضِف اختباراً (test) جديداً نلغي فيه الطلب قبل مرور 100 ميلي ثانية، ونتحقق من المخزن لنرى إن كان قد أُلغي.

```go
t.Run("tells store to cancel work if request is cancelled", func(t *testing.T) {
	data := "hello, world"
	store := &SpyStore{response: data}
	svr := Server(store)

	request := httptest.NewRequest(http.MethodGet, "/", nil)

	cancellingCtx, cancel := context.WithCancel(request.Context())
	time.AfterFunc(5*time.Millisecond, cancel)
	request = request.WithContext(cancellingCtx)

	response := httptest.NewRecorder()

	svr.ServeHTTP(response, request)

	if !store.cancelled {
		t.Error("store was not told to cancel")
	}
})
```

من [مدونة غو: Context](https://blog.golang.org/context)

> توفر الحزمة `context` دوالاً لاشتقاق قيم `Context` جديدة من قيم موجودة. وتشكّل هذه القيم شجرة: فحين يُلغى `Context`، تُلغى أيضاً كل قيم `Context` المشتقة منه.

من المهم أن تشتق سياقاتك كي ينتشر الإلغاء عبر مكدس الاستدعاءات كله لطلب معيّن.

ما نفعله هو اشتقاق `cancellingCtx` جديد من `request`، فيعيد لنا دالة `cancel`. ثم نجدول استدعاء تلك الدالة بعد 5 ميلي ثوانٍ باستعمال `time.AfterFunc`. وأخيراً نستعمل هذا السياق الجديد في طلبنا باستدعاء `request.WithContext`.

## حاول تشغيل الاختبار

يفشل الاختبار كما نتوقع.

```
--- FAIL: TestServer (0.00s)
    --- FAIL: TestServer/tells_store_to_cancel_work_if_request_is_cancelled (0.00s)
    	context_test.go:62: store was not told to cancel
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

تذكّر أن تلتزم بانضباط `TDD`. اكتب _أقل_ قدر من الشيفرة لجعل اختبارنا ينجح.

```go
func Server(store Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		store.Cancel()
		fmt.Fprint(w, store.Fetch())
	}
}
```

هذا يجعل الاختبار ينجح، لكنه لا يبدو جيداً، أليس كذلك؟ بالتأكيد لا ينبغي أن نستدعي `Cancel()` قبل الجلب في _كل طلب_.

بالانضباط كشفنا خللاً في اختباراتنا، وهذا أمر جيد!

سنحتاج إلى تحديث اختبار المسار الناجح ليؤكد أن الإلغاء لا يحدث.

```go
t.Run("returns data from store", func(t *testing.T) {
	data := "hello, world"
	store := &SpyStore{response: data}
	svr := Server(store)

	request := httptest.NewRequest(http.MethodGet, "/", nil)
	response := httptest.NewRecorder()

	svr.ServeHTTP(response, request)

	if response.Body.String() != data {
		t.Errorf(`got "%s", want "%s"`, response.Body.String(), data)
	}

	if store.cancelled {
		t.Error("it should not have cancelled the store")
	}
})
```

شغّل الاختبارين، وينبغي أن يفشل اختبار المسار الناجح الآن، فنُجبر على كتابة تنفيذ أكثر منطقية.

```go
func Server(store Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()

		data := make(chan string, 1)

		go func() {
			data <- store.Fetch()
		}()

		select {
		case d := <-data:
			fmt.Fprint(w, d)
		case <-ctx.Done():
			store.Cancel()
		}
	}
}
```

ما الذي فعلناه هنا؟

للقيمة `context` طريقة اسمها `Done()` تعيد قناة (channel) تُرسل إليها إشارة حين يكون السياق "منتهياً" أو "ملغى". نريد الاستماع إلى تلك الإشارة واستدعاء `store.Cancel` إن وصلتنا، لكننا نريد تجاهلها إن استطاعت `Store` أن تنفّذ `Fetch` قبلها.

ولإدارة ذلك، نشغّل `Fetch` في `goroutine` تكتب النتيجة في قناة جديدة `data`. ثم نستعمل `select` لنجعل العمليتين غير المتزامنتين تتسابقان فعلياً، فإما أن نكتب استجابة أو نستدعي `Cancel`.

## أعد الهيكلة

يمكننا إعادة هيكلة شيفرة اختبارنا قليلاً بإنشاء طرق توكيد على جاسوسنا

```go
type SpyStore struct {
	response  string
	cancelled bool
	t         *testing.T
}

func (s *SpyStore) assertWasCancelled() {
	s.t.Helper()
	if !s.cancelled {
		s.t.Error("store was not told to cancel")
	}
}

func (s *SpyStore) assertWasNotCancelled() {
	s.t.Helper()
	if s.cancelled {
		s.t.Error("store was told to cancel")
	}
}
```

تذكّر أن تمرر `*testing.T` عند إنشاء الجاسوس.

```go
func TestServer(t *testing.T) {
	data := "hello, world"

	t.Run("returns data from store", func(t *testing.T) {
		store := &SpyStore{response: data, t: t}
		svr := Server(store)

		request := httptest.NewRequest(http.MethodGet, "/", nil)
		response := httptest.NewRecorder()

		svr.ServeHTTP(response, request)

		if response.Body.String() != data {
			t.Errorf(`got "%s", want "%s"`, response.Body.String(), data)
		}

		store.assertWasNotCancelled()
	})

	t.Run("tells store to cancel work if request is cancelled", func(t *testing.T) {
		store := &SpyStore{response: data, t: t}
		svr := Server(store)

		request := httptest.NewRequest(http.MethodGet, "/", nil)

		cancellingCtx, cancel := context.WithCancel(request.Context())
		time.AfterFunc(5*time.Millisecond, cancel)
		request = request.WithContext(cancellingCtx)

		response := httptest.NewRecorder()

		svr.ServeHTTP(response, request)

		store.assertWasCancelled()
	})
}
```

هذا الأسلوب مقبول، لكن هل هو الأسلوب المعتاد في اللغة؟

هل من المنطقي أن يهتم خادم الويب لدينا بإلغاء `Store` يدوياً؟ وماذا لو كانت `Store` تعتمد أيضاً على عمليات بطيئة أخرى؟ سنضطر إلى التأكد من أن `Store.Cancel` تنشر الإلغاء بشكل صحيح إلى كل ما يعتمد عليها.

ومن أهم مزايا `context` أنها وسيلة متسقة لتوفير الإلغاء.

[من توثيق غو](https://golang.org/pkg/context/)

> ينبغي أن تُنشئ الطلبات الواردة إلى الخادم قيمة `Context`، وأن تقبل الاستدعاءات الصادرة إلى الخوادم قيمة `Context`. ويجب أن تمرر سلسلة استدعاءات الدوال بينهما قيمة `Context`، مع إمكانية استبدالها بقيمة مشتقة أُنشئت باستعمال `WithCancel` أو `WithDeadline` أو `WithTimeout` أو `WithValue`. وحين يُلغى `Context`، تُلغى أيضاً كل قيم `Context` المشتقة منه.

ومرة أخرى من [مدونة غو: Context](https://blog.golang.org/context):

> في Google، نشترط على مبرمجي غو أن يمرروا معامل `Context` كأول وسيط لكل دالة على مسار الاستدعاء بين الطلبات الواردة والصادرة. وهذا يتيح لشيفرة غو التي تطورها فرق مختلفة كثيرة أن تتكامل جيداً. كما يوفر تحكماً بسيطاً بالمهل الزمنية والإلغاء، ويضمن أن القيم الحرجة، مثل بيانات الاعتماد الأمنية، تنتقل عبر برامج غو كما ينبغي.

(توقف لحظة وفكّر في تبعات أن تضطر كل دالة إلى تمرير سياق، وفي مدى راحة ذلك.)

تشعر ببعض القلق؟ جيد. لنحاول مع ذلك اتباع هذا الأسلوب، فنمرر `context` إلى `Store` ونجعلها هي المسؤولة. وبهذا تستطيع أيضاً تمرير `context` إلى ما تعتمد عليه، فيكون كل منها مسؤولاً عن إيقاف نفسه.

## اكتب الاختبار أولاً

علينا تغيير اختباراتنا الحالية لأن مسؤولياتها تتغير. فالمسؤولية الوحيدة لمعالجنا الآن هي التأكد من أنه يمرر سياقاً إلى `Store` في المرحلة التالية، وأنه يعالج الخطأ (error) الذي سيأتي من `Store` حين تُلغى.

لنحدّث الواجهة `Store` لتُظهر المسؤوليات الجديدة.

```go
type Store interface {
	Fetch(ctx context.Context) (string, error)
}
```

احذف الشيفرة داخل معالجنا في الوقت الحالي

```go
func Server(store Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
	}
}
```

حدّث `SpyStore`

```go
type SpyStore struct {
	response string
	t        *testing.T
}

func (s *SpyStore) Fetch(ctx context.Context) (string, error) {
	data := make(chan string, 1)

	go func() {
		var result string
		for _, c := range s.response {
			select {
			case <-ctx.Done():
				log.Println("spy store got cancelled")
				return
			default:
				time.Sleep(10 * time.Millisecond)
				result += string(c)
			}
		}
		data <- result
	}()

	select {
	case <-ctx.Done():
		return "", ctx.Err()
	case res := <-data:
		return res, nil
	}
}
```

علينا أن نجعل جاسوسنا يتصرف كطريقة حقيقية تعمل مع `context`.

نحاكي عملية بطيئة نبني فيها النتيجة ببطء بإلحاق السلسلة النصية محرفاً محرفاً داخل `goroutine`. وحين تنهي الـ`goroutine` عملها تكتب السلسلة النصية في القناة `data`. وتستمع الـ`goroutine` إلى `ctx.Done`، وستوقف العمل إن أُرسلت إشارة في تلك القناة.

وأخيراً تستعمل الشيفرة تعليمة `select` أخرى لانتظار أن تنهي تلك الـ`goroutine` عملها أو أن يقع الإلغاء.

هذا يشبه أسلوبنا السابق، فنحن نستعمل أدوات التزامن (concurrency) الأساسية في غو لنجعل عمليتين غير متزامنتين تتسابقان لتحديد ما نعيده.

ستتبع أسلوباً مشابهاً حين تكتب دوالك وطرقك الخاصة التي تقبل `context`، فتأكد من أنك تفهم ما يجري.

وأخيراً يمكننا تحديث اختباراتنا. حوّل اختبار الإلغاء إلى تعليق كي نصلح اختبار المسار الناجح أولاً.

```go
t.Run("returns data from store", func(t *testing.T) {
	data := "hello, world"
	store := &SpyStore{response: data, t: t}
	svr := Server(store)

	request := httptest.NewRequest(http.MethodGet, "/", nil)
	response := httptest.NewRecorder()

	svr.ServeHTTP(response, request)

	if response.Body.String() != data {
		t.Errorf(`got "%s", want "%s"`, response.Body.String(), data)
	}
})
```

## حاول تشغيل الاختبار

```
=== RUN   TestServer/returns_data_from_store
--- FAIL: TestServer (0.00s)
    --- FAIL: TestServer/returns_data_from_store (0.00s)
    	context_test.go:22: got "", want "hello, world"
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func Server(store Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		data, _ := store.Fetch(r.Context())
		fmt.Fprint(w, data)
	}
}
```

ينبغي أن يكون مسارنا الناجح... ناجحاً. ويمكننا الآن إصلاح الاختبار الآخر.

## اكتب الاختبار أولاً

علينا أن نختبر أننا لا نكتب أي نوع من الاستجابة في حالة الخطأ. ولسوء الحظ لا يملك `httptest.ResponseRecorder` وسيلة لمعرفة ذلك، لذا سنصنع جاسوسنا الخاص لاختباره.

```go
type SpyResponseWriter struct {
	written bool
}

func (s *SpyResponseWriter) Header() http.Header {
	s.written = true
	return nil
}

func (s *SpyResponseWriter) Write([]byte) (int, error) {
	s.written = true
	return 0, errors.New("not implemented")
}

func (s *SpyResponseWriter) WriteHeader(statusCode int) {
	s.written = true
}
```

يحقق `SpyResponseWriter` الواجهة `http.ResponseWriter` لذا يمكننا استعماله في الاختبار.

```go
t.Run("tells store to cancel work if request is cancelled", func(t *testing.T) {
	data := "hello, world"
	store := &SpyStore{response: data, t: t}
	svr := Server(store)

	request := httptest.NewRequest(http.MethodGet, "/", nil)

	cancellingCtx, cancel := context.WithCancel(request.Context())
	time.AfterFunc(5*time.Millisecond, cancel)
	request = request.WithContext(cancellingCtx)

	response := &SpyResponseWriter{}

	svr.ServeHTTP(response, request)

	if response.written {
		t.Error("a response should not have been written")
	}
})
```

## حاول تشغيل الاختبار

```
=== RUN   TestServer
=== RUN   TestServer/tells_store_to_cancel_work_if_request_is_cancelled
--- FAIL: TestServer (0.01s)
    --- FAIL: TestServer/tells_store_to_cancel_work_if_request_is_cancelled (0.01s)
    	context_test.go:47: a response should not have been written
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func Server(store Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		data, err := store.Fetch(r.Context())

		if err != nil {
			return // todo: log error however you like
		}

		fmt.Fprint(w, data)
	}
}
```

نرى بعد هذا أن شيفرة الخادم صارت أبسط، لأنها لم تعد مسؤولة صراحةً عن الإلغاء، بل تمرر `context` فحسب وتعتمد على الدوال في المراحل التالية لاحترام أي إلغاء قد يحدث.

## الخلاصة

### ما تناولناه

- كيف تختبر معالج HTTP ألغى العميل طلبه.
- كيف تستعمل السياق لإدارة الإلغاء.
- كيف تكتب دالة تقبل `context` وتستعمله لإلغاء نفسها باستعمال الـ`goroutines` و`select` والقنوات.
- اتباع إرشادات Google في إدارة الإلغاء بنشر سياق خاص بنطاق الطلب عبر مكدس الاستدعاءات.
- كيف تصنع جاسوسك الخاص لـ`http.ResponseWriter` إن احتجت إليه.

### ماذا عن `context.Value`؟

لي ولـ[ميخال شتربا](https://faiface.github.io/post/context-should-go-away-go2/) رأي متشابه.

> إن استعملت `ctx.Value` في شركتي (غير الموجودة)، فأنت مطرود

دعا بعض المهندسين إلى تمرير القيم عبر `context` لأن ذلك _يبدو مريحاً_.

والراحة كثيراً ما تكون سبب الشيفرة السيئة.

المشكلة في `context.Values` أنها مجرد خريطة (map) غير محددة الأنواع، فلا يكون لديك أمان أنواع، وعليك معالجة احتمال ألا تحتوي على قيمتك أصلاً. كما عليك إنشاء اقتران بمفاتيح الخريطة بين وحدة وأخرى، وإن غيّر أحدهم شيئاً بدأت الأمور تتعطل.

باختصار، **إن احتاجت دالة إلى بعض القيم، فضعها كمعاملات (parameters) محددة الأنواع بدلاً من محاولة جلبها من `context.Value`**. فهذا يجعلها خاضعة للفحص الساكن وموثّقة ليراها الجميع.

#### لكن...

من ناحية أخرى، قد يكون من المفيد تضمين معلومات مستقلة عن الطلب في السياق، مثل معرّف التتبّع. فهذه المعلومات قد لا تحتاج إليها كل دالة في مكدس الاستدعاءات، وكانت ستجعل تواقيع دوالك فوضوية جداً.

[يقول جاك ليندامود: **ينبغي أن تُعلِم `Context.Value` لا أن تتحكم**](https://medium.com/@cep21/how-to-correctly-use-context-context-in-go-1-7-8f2c0fafdf39)

> محتوى `context.Value` مخصص لمن يصونون الشيفرة لا لمستخدميها. ولا ينبغي أبداً أن يكون مدخلاً مطلوباً للحصول على نتائج موثّقة أو متوقعة.

### مواد إضافية

- استمتعت حقاً بقراءة مقال [Context should go away for Go 2 لميخال شتربا](https://faiface.github.io/post/context-should-go-away-go2/). وحجته أن الاضطرار إلى تمرير `context` في كل مكان رائحة شيفرة سيئة، تشير إلى قصور في اللغة فيما يخص الإلغاء. ويقول إن من الأفضل لو حُلّت هذه المشكلة بطريقة ما على مستوى اللغة لا على مستوى مكتبة. وحتى يحدث ذلك، ستحتاج إلى `context` إن أردت إدارة العمليات طويلة الأمد.
- [وتشرح مدونة غو بمزيد من التفصيل دوافع العمل مع `context`، مع بعض الأمثلة](https://blog.golang.org/context)
