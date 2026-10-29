# التعليمة `select`

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/select)**

طُلب منك أن تكتب دالة (function) باسم `WebsiteRacer` تأخذ عنواني URL وتجعلهما "يتسابقان"، بإرسال طلب HTTP GET إلى كل منهما وإعادة العنوان الذي استجاب أولاً. وإن لم يستجب أي منهما خلال 10 ثوانٍ، فينبغي أن تعيد خطأً `error`.

سنستعمل لذلك:

- الحزمة `net/http` لإجراء استدعاءات HTTP.
- الحزمة `net/http/httptest` لمساعدتنا على اختبارها.
- الـ`goroutines`.
- التعليمة `select` لمزامنة العمليات.

## اكتب الاختبار أولاً

لنبدأ بشيء ساذج كي ننطلق.

```go
func TestRacer(t *testing.T) {
	slowURL := "http://www.facebook.com"
	fastURL := "http://www.quii.dev"

	want := fastURL
	got := Racer(slowURL, fastURL)

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}
```

نعرف أن هذا ليس مثالياً وأن فيه مشكلات، لكنه بداية. فمن المهم ألا ننشغل كثيراً بجعل الأمور مثالية من المرة الأولى.

## حاول تشغيل الاختبار

`./racer_test.go:14:9: undefined: Racer`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

```go
func Racer(a, b string) (winner string) {
	return
}
```

`racer_test.go:25: got '', want 'http://www.quii.dev'`

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func Racer(a, b string) (winner string) {
	startA := time.Now()
	http.Get(a)
	aDuration := time.Since(startA)

	startB := time.Now()
	http.Get(b)
	bDuration := time.Since(startB)

	if aDuration < bDuration {
		return a
	}

	return b
}
```

نفعل ما يلي لكل عنوان URL على حدة:

1. نستعمل `time.Now()` لتسجيل الوقت قبل أن نحاول جلب `URL` مباشرة.
1. ثم نستعمل [`http.Get`](https://golang.org/pkg/net/http/#Client.Get) لمحاولة تنفيذ طلب HTTP من نوع `GET` إلى `URL`. تعيد هذه الدالة [`http.Response`](https://golang.org/pkg/net/http/#Response) و`error`، لكن هذه القيم لا تهمنا حتى الآن.
1. تأخذ `time.Since` وقت البدء وتعيد الفرق على شكل `time.Duration`.

بعد ذلك نقارن المدد ببساطة لنرى أيها الأسرع.

### المشكلات

قد ينجح الاختبار (test) لديك بهذا وقد لا ينجح. فالمشكلة أننا نتصل بمواقع حقيقية لاختبار منطقنا الخاص.

اختبار الشيفرة (code) التي تستعمل HTTP شائع جداً، حتى إن في المكتبة القياسية لغو (Go) أدوات تساعدك على اختبارها.

تناولنا في فصلي المحاكاة وحقن التبعية كيف أننا في الوضع المثالي لا نريد الاعتماد على خدمات خارجية لاختبار شيفرتنا، لأنها قد تكون

- بطيئة
- متقلبة
- لا تسمح باختبار الحالات الحدّية

في المكتبة القياسية حزمة اسمها [`net/http/httptest`](https://golang.org/pkg/net/http/httptest/) تتيح للمستخدمين إنشاء خادم HTTP وهمي بسهولة.

لنغيّر اختباراتنا لتستعمل البدائل الوهمية (mocks)، كي تكون لدينا خوادم موثوقة نتحكم بها ونختبر عليها.

```go
func TestRacer(t *testing.T) {

	slowServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(20 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))

	fastServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	slowURL := slowServer.URL
	fastURL := fastServer.URL

	want := fastURL
	got := Racer(slowURL, fastURL)

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}

	slowServer.Close()
	fastServer.Close()
}
```

قد تبدو الصياغة مزدحمة بعض الشيء، لكن خذ وقتك فحسب.

تأخذ `httptest.NewServer` قيمة `http.HandlerFunc` نمررها عبر _دالة مجهولة_.

والنوع `http.HandlerFunc` يبدو هكذا: `type HandlerFunc func(ResponseWriter, *Request)`.

كل ما يقوله في الحقيقة أنه يحتاج إلى دالة تأخذ `ResponseWriter` و`Request`، وهذا ليس مفاجئاً في خادم HTTP على الإطلاق.

يتضح أنه لا سحر إضافياً هنا، **فهذه أيضاً هي الطريقة التي تكتب بها خادم HTTP _حقيقياً_ في غو**. والفرق الوحيد أننا نغلّفه في `httptest.NewServer` الذي يسهّل استعماله في الاختبار، إذ يجد منفذاً مفتوحاً للاستماع عليه، ثم تستطيع إغلاقه حين تنتهي من اختبارك.

داخل الخادمين، نجعل الخادم البطيء ينام قليلاً بـ`time.Sleep` حين يصلنا طلب، كي يكون أبطأ من الآخر. ثم يكتب كلا الخادمين استجابة `OK` إلى المستدعي بـ`w.WriteHeader(http.StatusOK)`.

إن أعدت تشغيل الاختبار، فسينجح الآن بالتأكيد، وينبغي أن يكون أسرع. جرّب التلاعب بمدد النوم هذه لتُفشل الاختبار عمداً.

## أعد الهيكلة

لدينا بعض الازدواجية في شيفرة الإنتاج وفي شيفرة الاختبار معاً.

```go
func Racer(a, b string) (winner string) {
	aDuration := measureResponseTime(a)
	bDuration := measureResponseTime(b)

	if aDuration < bDuration {
		return a
	}

	return b
}

func measureResponseTime(url string) time.Duration {
	start := time.Now()
	http.Get(url)
	return time.Since(start)
}
```

إزالة التكرار هذه تجعل شيفرة `Racer` أسهل قراءة بكثير.

```go
func TestRacer(t *testing.T) {

	slowServer := makeDelayedServer(20 * time.Millisecond)
	fastServer := makeDelayedServer(0 * time.Millisecond)

	defer slowServer.Close()
	defer fastServer.Close()

	slowURL := slowServer.URL
	fastURL := fastServer.URL

	want := fastURL
	got := Racer(slowURL, fastURL)

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}

func makeDelayedServer(delay time.Duration) *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(delay)
		w.WriteHeader(http.StatusOK)
	}))
}
```

أعدنا هيكلة إنشاء خوادمنا المزيفة بنقله إلى دالة باسم `makeDelayedServer`، لإخراج بعض الشيفرة غير المهمة من الاختبار وتقليل التكرار.

### التعليمة `defer`

حين تسبق استدعاء دالة بالكلمة `defer`، فإنها ستستدعي تلك الدالة _في نهاية الدالة التي تحتويها_.

ستحتاج أحياناً إلى تنظيف الموارد، كإغلاق ملف، أو كما في حالتنا إغلاق خادم كي لا يواصل الاستماع على منفذ.

تريد أن يُنفَّذ هذا في نهاية الدالة، لكن مع إبقاء التعليمة قرب المكان الذي أنشأت فيه الخادم، لفائدة من سيقرأ الشيفرة مستقبلاً.

إعادة الهيكلة التي أجريناها تحسين، وهي حل معقول بالنظر إلى ميزات غو التي تناولناها حتى الآن، لكن يمكننا جعل الحل أبسط.

### مزامنة العمليات

- لماذا نختبر سرعات المواقع واحداً تلو الآخر، وغو بارعة في التزامن (concurrency)؟ ينبغي أن نستطيع التحقق من كليهما في الوقت نفسه.
- لا تهمنا حقاً _أزمنة الاستجابة الدقيقة_ للطلبات، بل نريد فقط أن نعرف أيها يعود أولاً.

لفعل ذلك، سنقدّم تركيباً لغوياً جديداً اسمه `select`، يساعدنا على مزامنة العمليات بسهولة ووضوح كبيرين.

```go
func Racer(a, b string) (winner string) {
	select {
	case <-ping(a):
		return a
	case <-ping(b):
		return b
	}
}

func ping(url string) chan struct{} {
	ch := make(chan struct{})
	go func() {
		http.Get(url)
		close(ch)
	}()
	return ch
}
```

#### الدالة `ping`

عرّفنا دالة باسم `ping` تنشئ `chan struct{}` وتعيدها.

في حالتنا، لا _يهمنا_ نوع ما يُرسل إلى القناة (channel)، _بل نريد فقط الإشارة إلى أننا انتهينا_، وإغلاق القناة يؤدي ذلك تماماً!

لماذا `struct{}` وليس نوعاً آخر مثل `bool`؟ لأن `chan struct{}` هو أصغر نوع بيانات متاح من ناحية الذاكرة، فلا
نحصل على أي تخصيص للذاكرة مقارنة بـ`bool`. وبما أننا نغلق القناة ولا نرسل عليها شيئاً، فلماذا نخصص أي شيء؟

داخل الدالة نفسها، نبدأ `goroutine` سترسل إشارة إلى تلك القناة بمجرد أن ننتهي من `http.Get(url)`.

##### أنشئ القنوات دائماً بـ`make`

لاحظ أن علينا استعمال `make` عند إنشاء قناة، بدلاً من أن نكتب مثلاً `var ch chan struct{}`. فحين تستعمل `var` يُهيَّأ المتغير بالقيمة "الصفرية" لنوعه. فهي `""` للنوع `string`، و0 للنوع `int`، وهكذا.

والقيمة الصفرية للقنوات هي `nil`، وإن حاولت الإرسال إليها بـ`<-` فستُحجب إلى الأبد، لأنك لا تستطيع الإرسال إلى قنوات `nil`

[يمكنك أن ترى هذا عملياً في ساحة تجارب غو](https://play.golang.org/p/IIbeAox5jKA)
#### التعليمة `select`

تذكر من فصل التزامن أنك تستطيع انتظار إرسال القيم إلى قناة بكتابة `myVar := <-ch`. وهذا استدعاء _حاجب_، لأنك تنتظر قيمة.

تتيح لك `select` الانتظار على قنوات _متعددة_. فأول قناة ترسل قيمة "تفوز"، وتُنفَّذ الشيفرة الواقعة تحت `case` الخاصة بها.

نستعمل `ping` في `select` لإعداد قناتين، واحدة لكل `URL`. وأي منهما تكتب إلى قناتها أولاً، تُنفَّذ شيفرتها في `select`، فيُعاد `URL` الخاص بها (ويكون هو الفائز).

بعد هذه التغييرات صار القصد من شيفرتنا واضحاً جداً، وصار التنفيذ في الحقيقة أبسط.

### المهل الزمنية

متطلبنا الأخير كان إعادة خطأ (error) إن استغرقت `Racer` أكثر من 10 ثوانٍ.

## اكتب الاختبار أولاً

```go
func TestRacer(t *testing.T) {
	t.Run("compares speeds of servers, returning the url of the fastest one", func(t *testing.T) {
		slowServer := makeDelayedServer(20 * time.Millisecond)
		fastServer := makeDelayedServer(0 * time.Millisecond)

		defer slowServer.Close()
		defer fastServer.Close()

		slowURL := slowServer.URL
		fastURL := fastServer.URL

		want := fastURL
		got, _ := Racer(slowURL, fastURL)

		if got != want {
			t.Errorf("got %q, want %q", got, want)
		}
	})

	t.Run("returns an error if a server doesn't respond within 10s", func(t *testing.T) {
		serverA := makeDelayedServer(11 * time.Second)
		serverB := makeDelayedServer(12 * time.Second)

		defer serverA.Close()
		defer serverB.Close()

		_, err := Racer(serverA.URL, serverB.URL)

		if err == nil {
			t.Error("expected an error but didn't get one")
		}
	})
}
```

جعلنا خوادم الاختبار تستغرق أكثر من 10 ثوانٍ لتستجيب كي نختبر هذا السيناريو، ونتوقع الآن أن تعيد `Racer` قيمتين: عنوان URL الفائز (الذي نتجاهله في هذا الاختبار بـ`_`)، و`error`.

لاحظ أننا عالجنا أيضاً الخطأ المعاد في اختبارنا الأصلي، ونستعمل `_` حالياً لضمان أن الاختبارات ستعمل.

## حاول تشغيل الاختبار

`./racer_test.go:37:10: assignment mismatch: 2 variables but Racer returns 1 value`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

```go
func Racer(a, b string) (winner string, error error) {
	select {
	case <-ping(a):
		return a, nil
	case <-ping(b):
		return b, nil
	}
}
```

غيّر توقيع `Racer` لتعيد الفائز و`error`، وأعد `nil` في الحالات الناجحة.

سيعترض المصرِّف (compiler) على أن _اختبارك الأول_ لا ينتظر إلا قيمة واحدة، فغيّر ذلك السطر إلى `got, err := Racer(slowURL, fastURL)`، مع العلم أن علينا التحقق من أننا _لا_ نحصل على خطأ في السيناريو الناجح.

إن شغّلته الآن فسيفشل بعد 11 ثانية.

```
--- FAIL: TestRacer (12.00s)
    --- FAIL: TestRacer/returns_an_error_if_a_server_doesn't_respond_within_10s (12.00s)
        racer_test.go:40: expected an error but didn't get one
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func Racer(a, b string) (winner string, error error) {
	select {
	case <-ping(a):
		return a, nil
	case <-ping(b):
		return b, nil
	case <-time.After(10 * time.Second):
		return "", fmt.Errorf("timed out waiting for %s and %s", a, b)
	}
}
```

الدالة `time.After` مفيدة جداً عند استعمال `select`. فمع أن ذلك لم يحدث في حالتنا، فقد تكتب شيفرة تُحجب إلى الأبد إن لم تُعِد القنوات التي تستمع إليها أي قيمة. تعيد `time.After` قناة `chan` (مثل `ping`)، وترسل عليها إشارة بعد مرور المدة التي تحددها.

وهذا مثالي لنا؛ فإن استطاعت `a` أو `b` أن تعود فإنها تفوز، لكن إن وصلنا إلى 10 ثوانٍ فسترسل `time.After` إشارة ونعيد `error`.

### الاختبارات البطيئة

المشكلة لدينا أن هذا الاختبار يستغرق 10 ثوانٍ ليعمل. ولمنطق بهذه البساطة، لا يبدو هذا جيداً.

ما يمكننا فعله هو جعل المهلة الزمنية قابلة للضبط. فيمكننا في اختبارنا استعمال مهلة قصيرة جداً، وحين تُستعمل الشيفرة في العالم الحقيقي يمكن ضبطها على 10 ثوانٍ.

```go
func Racer(a, b string, timeout time.Duration) (winner string, error error) {
	select {
	case <-ping(a):
		return a, nil
	case <-ping(b):
		return b, nil
	case <-time.After(timeout):
		return "", fmt.Errorf("timed out waiting for %s and %s", a, b)
	}
}
```

لن تُصرَّف اختباراتنا الآن لأننا لا نقدّم مهلة زمنية.

قبل أن نسارع إلى إضافة هذه القيمة الافتراضية إلى الاختبارين، لـ_نصغِ إليهما_.

- هل تهمنا المهلة الزمنية في الاختبار "الناجح"؟
- كانت المتطلبات صريحة بشأن المهلة الزمنية.

وبناءً على هذا، لنُجرِ قليلاً من إعادة الهيكلة (refactoring) بما يراعي اختباراتنا ومستخدمي شيفرتنا معاً.

```go
var tenSecondTimeout = 10 * time.Second

func Racer(a, b string) (winner string, error error) {
	return ConfigurableRacer(a, b, tenSecondTimeout)
}

func ConfigurableRacer(a, b string, timeout time.Duration) (winner string, error error) {
	select {
	case <-ping(a):
		return a, nil
	case <-ping(b):
		return b, nil
	case <-time.After(timeout):
		return "", fmt.Errorf("timed out waiting for %s and %s", a, b)
	}
}
```

يستطيع مستخدمونا واختبارنا الأول استعمال `Racer` (التي تستعمل `ConfigurableRacer` في الخفاء)، ويستطيع اختبار المسار الفاشل استعمال `ConfigurableRacer`.

```go
func TestRacer(t *testing.T) {

	t.Run("compares speeds of servers, returning the url of the fastest one", func(t *testing.T) {
		slowServer := makeDelayedServer(20 * time.Millisecond)
		fastServer := makeDelayedServer(0 * time.Millisecond)

		defer slowServer.Close()
		defer fastServer.Close()

		slowURL := slowServer.URL
		fastURL := fastServer.URL

		want := fastURL
		got, err := Racer(slowURL, fastURL)

		if err != nil {
			t.Fatalf("did not expect an error but got one %v", err)
		}

		if got != want {
			t.Errorf("got %q, want %q", got, want)
		}
	})

	t.Run("returns an error if a server doesn't respond within the specified time", func(t *testing.T) {
		server := makeDelayedServer(25 * time.Millisecond)

		defer server.Close()

		_, err := ConfigurableRacer(server.URL, server.URL, 20*time.Millisecond)

		if err == nil {
			t.Error("expected an error but didn't get one")
		}
	})
}
```

أضفت تحققاً أخيراً في الاختبار الأول للتأكد من أننا لا نحصل على `error`.

## الخلاصة

### التعليمة `select`

- تساعدك على الانتظار على قنوات متعددة.
- ستريد أحياناً تضمين `time.After` في إحدى حالات `cases` لمنع نظامك من الحجب إلى الأبد.

### الحزمة `httptest`

- طريقة مريحة لإنشاء خوادم اختبار كي تكون لديك اختبارات موثوقة يمكن التحكم بها.
- تستعمل الواجهات (interfaces) نفسها التي تستعملها خوادم `net/http` "الحقيقية"، وهذا متسق ويقلل ما عليك تعلّمه.
