# الحزمة `sync`

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/sync)**

نريد صنع عدّاد آمن للاستعمال المتزامن.

سنبدأ بعدّاد غير آمن، ونتحقق من أن سلوكه يعمل في بيئة أحادية الخيط.

ثم نختبر عدم أمانه، بجعل عدة `goroutines` تحاول استعمال العدّاد عبر اختبار (test)، ثم نصلحه.

## اكتب الاختبار أولاً

نريد أن تعطينا واجهتنا البرمجية طريقة (method) لزيادة العدّاد ثم استرجاع قيمته.

```go
func TestCounter(t *testing.T) {
	t.Run("incrementing the counter 3 times leaves it at 3", func(t *testing.T) {
		counter := Counter{}
		counter.Inc()
		counter.Inc()
		counter.Inc()

		if counter.Value() != 3 {
			t.Errorf("got %d, want %d", counter.Value(), 3)
		}
	})
}
```

## حاول تشغيل الاختبار

```
./sync_test.go:9:14: undefined: Counter
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

لنعرّف `Counter`.

```go
type Counter struct {
}
```

حاول مجدداً، وسيفشل بما يلي

```
./sync_test.go:14:10: counter.Inc undefined (type Counter has no field or method Inc)
./sync_test.go:18:13: counter.Value undefined (type Counter has no field or method Value)
```

ولكي يعمل الاختبار أخيراً، يمكننا تعريف هذه الطرق

```go
func (c *Counter) Inc() {

}

func (c *Counter) Value() int {
	return 0
}
```

ينبغي أن يعمل الآن ويفشل

```
=== RUN   TestCounter
=== RUN   TestCounter/incrementing_the_counter_3_times_leaves_it_at_3
--- FAIL: TestCounter (0.00s)
    --- FAIL: TestCounter/incrementing_the_counter_3_times_leaves_it_at_3 (0.00s)
    	sync_test.go:27: got 0, want 3
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

ينبغي أن يكون هذا بسيطاً جداً لخبراء في غو (Go) مثلنا. علينا الاحتفاظ بحالة للعدّاد في نوع بياناتنا، ثم زيادتها مع كل استدعاء لـ`Inc`

```go
type Counter struct {
	value int
}

func (c *Counter) Inc() {
	c.value++
}

func (c *Counter) Value() int {
	return c.value
}
```

## أعد الهيكلة

ليس هناك الكثير مما يمكن إعادة هيكلته، لكن بما أننا سنكتب مزيداً من الاختبارات حول `Counter`، فسنكتب دالة توكيد صغيرة `assertCount` كي يُقرأ الاختبار بوضوح أكبر.

```go
t.Run("incrementing the counter 3 times leaves it at 3", func(t *testing.T) {
	counter := Counter{}
	counter.Inc()
	counter.Inc()
	counter.Inc()

	assertCounter(t, counter, 3)
})
```
```go
func assertCounter(t testing.TB, got Counter, want int) {
	t.Helper()
	if got.Value() != want {
		t.Errorf("got %d, want %d", got.Value(), want)
	}
}
```

## الخطوات التالية

كان ذلك سهلاً بما يكفي، لكن لدينا الآن متطلب بأن يكون العدّاد آمناً للاستعمال في بيئة متزامنة. وسنحتاج إلى كتابة اختبار فاشل لاختبار ذلك.

## اكتب الاختبار أولاً

```go
t.Run("it runs safely concurrently", func(t *testing.T) {
	wantedCount := 1000
	counter := Counter{}

	var wg sync.WaitGroup
	wg.Add(wantedCount)

	for i := 0; i < wantedCount; i++ {
		go func() {
			counter.Inc()
			wg.Done()
		}()
	}
	wg.Wait()

	assertCounter(t, counter, wantedCount)
})
```

سيمر هذا على `wantedCount` ويُطلق `goroutine` تستدعي `counter.Inc()`.

نستعمل [`sync.WaitGroup`](https://golang.org/pkg/sync/#WaitGroup)، وهي وسيلة مريحة لمزامنة العمليات المتزامنة.

> تنتظر `WaitGroup` مجموعة من الـ`goroutines` حتى تنتهي. تستدعي الـ`goroutine` الرئيسية `Add` لتحديد عدد الـ`goroutines` التي ستنتظرها. ثم تعمل كل واحدة منها وتستدعي `Done` حين تنتهي. وفي الوقت نفسه، يمكن استعمال `Wait` للحجب حتى تنتهي كل الـ`goroutines`.

بانتظار انتهاء `wg.Wait()` قبل إجراء توكيداتنا (assertions)، نتأكد من أن كل الـ`goroutines` قد حاولت تنفيذ `Inc` على `Counter`.

## حاول تشغيل الاختبار

```
=== RUN   TestCounter/it_runs_safely_concurrently
--- FAIL: TestCounter (0.00s)
    --- FAIL: TestCounter/it_runs_safely_concurrently (0.00s)
    	sync_test.go:26: got 939, want 1000
FAIL
```

_على الأرجح_ سيفشل الاختبار بعدد مختلف، لكنه يبيّن على أي حال أن العدّاد لا يعمل حين تحاول عدة `goroutines` تغيير قيمته في الوقت نفسه.

### لماذا يحدث هذا؟

يبدو `c.value++` عملية واحدة غير قابلة للتجزئة، لكنه ليس كذلك. فهو اختصار لشيء أقرب إلى:

```go
tmp := c.value // 1. read
tmp = tmp + 1  // 2. increment
c.value = tmp  // 3. write
```

كل خطوة من هذه الخطوات الثلاث عملية منفصلة، ووقت تشغيل غو حرّ في التبديل بين الـ`goroutines` في أي لحظة بينها. فإن استدعت اثنتان من الـ`goroutines` الطريقة `Inc` في الوقت نفسه تقريباً، فقد تتداخل خطواتهما، مثلاً:

```
goroutine A: reads c.value (0)
goroutine B: reads c.value (0)
goroutine A: increments its copy to 1
goroutine B: increments its copy to 1
goroutine A: writes c.value = 1
goroutine B: writes c.value = 1
```

استدعت كل `goroutine` من الاثنتين `Inc` مرة واحدة، فكنا نريد أن تصبح قيمة `c.value` في النهاية `2`، لكنها تصبح `1`. فقد ضاعت إحدى الزيادتين بصمت، لأن الـ`goroutines` كلتيهما قرأتا قيمة البداية نفسها قبل أن تكتب أي منهما نتيجتها. وهذا ما يُسمى _تسابقاً_ (race condition)، ومع ألف `goroutine` تتسابق كلها للقراءة والزيادة والكتابة في آن واحد، فلا عجب أن تضيع بعض تلك الزيادات.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

من الحلول البسيطة إضافة قفل إلى `Counter`، يضمن ألا تزيد العدّاد إلا `goroutine` واحدة في كل مرة. ويوفر [`Mutex`](https://golang.org/pkg/sync/#Mutex) في غو قفلاً كهذا:

>القيمة `Mutex` قفل للاستبعاد المتبادل. والقيمة الصفرية لـ`Mutex` قفل غير مقفول.

```go
type Counter struct {
	mu    sync.Mutex
	value int
}

func (c *Counter) Inc() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.value++
}
```

معنى هذا أن أي `goroutine` تستدعي `Inc` ستحصل على القفل على `Counter` إن كانت الأولى. وعلى كل الـ`goroutines` الأخرى أن تنتظر حتى يُفتح القفل بـ`Unlock` قبل أن تحصل على الوصول.

إن أعدت تشغيل الاختبار الآن، فينبغي أن ينجح، لأن على كل `goroutine` أن تنتظر دورها قبل إجراء أي تغيير.

## رأيت أمثلة أخرى تُضمَّن فيها `sync.Mutex` داخل البنية.

قد ترى أمثلة كهذه

```go
type Counter struct {
	sync.Mutex
	value int
}
```

قد يقول قائل إن هذا يجعل الشيفرة (code) أكثر أناقة بعض الشيء.

```go
func (c *Counter) Inc() {
	c.Lock()
	defer c.Unlock()
	c.value++
}
```

هذا _يبدو_ جميلاً، لكن مع أن البرمجة مجال ذاتي إلى حد بعيد، فهذا **سيئ وخاطئ**.

ينسى الناس أحياناً أن تضمين الأنواع يعني أن طرق النوع المضمَّن تصبح _جزءاً من الواجهة العامة_، وكثيراً ما لن تريد ذلك. تذكّر أن علينا الحذر الشديد مع واجهاتنا البرمجية العامة، فاللحظة التي نجعل فيها شيئاً عاماً هي اللحظة التي تستطيع فيها شيفرة أخرى أن تقترن به. ونحن نريد دائماً تجنب الاقتران غير الضروري.

كشف `Lock` و`Unlock` محيّر في أحسن الأحوال، وقد يكون في أسوئها ضاراً جداً ببرنامجك إن بدأ مستدعو نوعك باستدعاء هذه الطرق.

![يوضح كيف يمكن لمستخدم هذه الواجهة البرمجية أن يغيّر حالة القفل بشكل خاطئ](https://i.imgur.com/SWYNpwm.png)

_تبدو هذه فكرة سيئة حقاً_

## نسخ الأقفال

ينجح اختبارنا، لكن شيفرتنا ما زالت خطرة بعض الشيء

إن شغّلت `go vet` على شيفرتك، فينبغي أن تحصل على خطأ كالتالي

```
sync/v2/sync_test.go:16: call of assertCounter copies lock value: v1.Counter contains sync.Mutex
sync/v2/sync_test.go:39: assertCounter passes lock by value: v1.Counter contains sync.Mutex
```

نظرة إلى توثيق [`sync.Mutex`](https://golang.org/pkg/sync/#Mutex) تخبرنا بالسبب

> يجب ألا تُنسخ قيمة `Mutex` بعد أول استعمال لها.

حين نمرر `Counter` (بالقيمة) إلى `assertCounter`، فسيحاول إنشاء نسخة من القفل.

لحل ذلك ينبغي أن نمرر مؤشراً (pointer) إلى `Counter` بدلاً منه، لذا غيّر توقيع `assertCounter`

```go
func assertCounter(t testing.TB, got *Counter, want int)
```

لن تُصرَّف اختباراتنا بعد الآن لأننا نحاول تمرير `Counter` بدلاً من `*Counter`. ولحل ذلك، أفضّل إنشاء دالة بانية تُظهر لقراء واجهتك البرمجية أن من الأفضل ألا يهيّئوا النوع بأنفسهم.

```go
func NewCounter() *Counter {
	return &Counter{}
}
```

استعمل هذه الدالة في اختباراتك عند تهيئة `Counter`.

## بديل آخر: الحزمة sync/atomic

النوع `Mutex` أداة عامة الغرض، فهو يستطيع حماية أي عدد من الحقول وأي ثابت منطقي (invariant) يربط بينها، ما دمت تتذكر استدعاء `Lock` و`Unlock` حول كل وصول. لكن `Counter` لدينا من أبسط ما يمكن أن تكون عليه الحالة المشتركة: عدد صحيح واحد تزيده عدة `goroutines`. ولهذا النوع من الحالات بالضبط، توفر الحزمة [`sync/atomic`](https://pkg.go.dev/sync/atomic) أنواعاً مثل [`atomic.Int64`](https://pkg.go.dev/sync/atomic#Int64) تمنحك وصولاً متزامناً آمناً إلى قيمة واحدة دون قفل منفصل على الإطلاق:

```go
type Counter struct {
	value atomic.Int64
}

func NewCounter() *Counter {
	return &Counter{}
}

func (c *Counter) Inc() {
	c.value.Add(1)
}

func (c *Counter) Value() int64 {
	return c.value.Load()
}
```

لا `Mutex`، ولا `Lock` أو `Unlock`، ومع ذلك يظل استدعاء `Inc` آمناً من أي عدد تشاء من الـ`goroutines` في آن واحد، والاختبار نفسه الذي كتبناه سابقاً ينجح دون تغيير. ففي الخفاء تستعمل هذه الأنواع تعليمات منخفضة المستوى في المعالج لتجعل الزيادة نفسها ذرّية (atomic)، وهذا عادةً أسرع من `Mutex` في الحالات البسيطة كهذه. كما أن `atomic.Int64` (وأشقاءه، مثل `atomic.Int32` و`atomic.Bool`) لا يمكن استعمالها استعمالاً خاطئاً على النحو الذي كان ممكناً مع استدعاءات الدوال الخام من نوع `atomic.AddInt64(&x, 1)` في إصدارات غو الأقدم، فلا يمكنك أن تنسى تمرير مؤشر، ولا يمكنك قراءة الحقل خطأً دون المرور بـ`Load`.

استعمل أنواع `sync/atomic` حين تحمي قيمة واحدة، واستعمل `Mutex` حين تحتاج إلى إبقاء عدة حقول، أو ثابت منطقي يربط بينها، متسقة معاً.

## الخلاصة

تناولنا بعض الأشياء من [الحزمة sync](https://golang.org/pkg/sync/)

- يتيح لنا `Mutex` إضافة أقفال إلى بياناتنا
- و`WaitGroup` وسيلة لانتظار الـ`goroutines` حتى تنهي أعمالها
- وتوفر الحزمة `sync/atomic` وصولاً آمناً بلا أقفال إلى القيم المفردة، ويستحق اللجوء إليها حين يكون `Mutex` كامل مبالغة

### متى تستعمل الأقفال بدلاً من القنوات والـ`goroutines`؟

[تناولنا الـ`goroutines` سابقاً في فصل التزامن الأول](concurrency.md)، وهي تتيح لنا كتابة شيفرة متزامنة آمنة، فلماذا تستعمل الأقفال؟
[في ويكي غو صفحة مخصصة لهذا الموضوع: Mutex Or Channel](https://go.dev/wiki/MutexOrChannel)

> من الأخطاء الشائعة لدى المبتدئين في غو الإفراط في استعمال القنوات والـ`goroutines` لمجرد أن ذلك ممكن، و/أو لأنه ممتع. لا تخشَ استعمال `sync.Mutex` إن كان الأنسب لمشكلتك. فغو لغة عملية تتيح لك استعمال الأدوات التي تحل مشكلتك على أفضل وجه، ولا تفرض عليك أسلوباً واحداً في كتابة الشيفرة.

بعبارة أخرى:

- **استعمل القنوات (channels) حين تنقل ملكية البيانات**
- **استعمل الأقفال لإدارة الحالة**

### الأداة `go vet`

تذكّر أن تستعمل `go vet` في سكربتات البناء لديك، لأنها قد تنبهك إلى بعض الأخطاء البرمجية الخفية في شيفرتك قبل أن تصيب مستخدميك المساكين.

### لا تستعمل التضمين لمجرد أنه مريح

- فكّر في أثر التضمين على واجهتك البرمجية العامة.
- هل تريد _حقاً_ كشف هذه الطرق وجعل الناس يربطون شيفرتهم بها؟
- وفيما يخص الأقفال، قد يكون هذا كارثياً بطرق غريبة يصعب التنبؤ بها. تخيّل شيفرة خبيثة تفتح قفلاً في غير وقته؛ فهذا سيسبب أخطاء برمجية غريبة جداً يصعب تتبّعها.
