# القارئ الواعي بالسياق

**[تجد كل الشيفرة هنا](https://github.com/quii/learn-go-with-tests/tree/main/q-and-a/context-aware-reader)**

يبيّن هذا الفصل كيف نبني بالاختبارات قارئاً `io.Reader` واعياً بالسياق، كما كتبه مات راير وديفيد هيرنانديز في [The Pace Dev Blog](https://pace.dev/blog/2020/02/03/context-aware-ioreader-for-golang-by-mat-ryer).

## قارئ واعٍ بالسياق؟

أولاً، تمهيد سريع عن `io.Reader`.

إن كنت قد قرأت فصولاً أخرى من هذا الكتاب، فستكون قد صادفت `io.Reader` حين فتحنا الملفات، وحين رمّزنا JSON، وفي مهام شائعة أخرى. إنه تجريد بسيط فوق قراءة البيانات من _شيء ما_

```go
type Reader interface {
	Read(p []byte) (n int, err error)
}
```

باستعمال `io.Reader` يمكنك الاستفادة كثيراً من إعادة الاستعمال في المكتبة القياسية، فهو تجريد شائع الاستعمال جداً (مع نظيره `io.Writer`)

### واعٍ بالسياق؟

[في فصل سابق](context.md) ناقشنا كيف يمكننا استعمال `context` لتوفير الإلغاء. وهذا مفيد خصوصاً إن كنت تنفّذ مهام قد تكون مكلفة حسابياً، وتريد أن تستطيع إيقافها.

حين تستعمل `io.Reader` لا تكون لديك أي ضمانات بشأن السرعة، فقد يستغرق نانوثانية واحدة أو مئات الساعات. وقد تجد من المفيد أن تستطيع إلغاء هذا النوع من المهام في تطبيقك، وهذا ما كتب عنه مات وديفيد.

فقد جمعا تجريدين بسيطين (`context.Context` و`io.Reader`) لحل هذه المشكلة.

لنحاول بناء بعض الوظائف بـ`TDD` كي نستطيع تغليف `io.Reader` بحيث يمكن إلغاؤه.

يطرح اختبار هذا تحدياً مثيراً للاهتمام. فحين تستعمل `io.Reader` فإنك تقدّمه عادةً إلى دالة (function) أخرى ولا تهتم حقاً بالتفاصيل، مثل `json.NewDecoder` أو `io.ReadAll`.

ما نريد إثباته شيء مثل

> بمعلومية `io.Reader` فيه "ABCDEF"، حين أرسل إشارة إلغاء في منتصف الطريق، ثم أحاول مواصلة القراءة، لا أحصل على أي شيء آخر، فكل ما أحصل عليه هو "ABC"

لننظر في الواجهة (interface) مجدداً.

```go
type Reader interface {
	Read(p []byte) (n int, err error)
}
```

ستقرأ الطريقة (method) `Read` في `Reader` المحتويات التي لديها إلى `[]byte` نقدّمها.

لذا بدلاً من قراءة كل شيء، يمكننا:

 - تقديم مصفوفة بايتات ثابتة الحجم لا تتسع لكل المحتويات
 - إرسال إشارة إلغاء
 - محاولة القراءة مجدداً، وينبغي أن يعيد هذا خطأً مع قراءة 0 بايت

في الوقت الحالي، لنكتب فقط اختبار "مسار ناجح" لا إلغاء فيه، لمجرد أن نألف المشكلة دون الحاجة إلى كتابة أي شيفرة إنتاج بعد.

```go
func TestContextAwareReader(t *testing.T) {
	t.Run("lets just see how a normal reader works", func(t *testing.T) {
		rdr := strings.NewReader("123456")
		got := make([]byte, 3)
		_, err := rdr.Read(got)

		if err != nil {
			t.Fatal(err)
		}

		assertBufferHas(t, got, "123")

		_, err = rdr.Read(got)

		if err != nil {
			t.Fatal(err)
		}

		assertBufferHas(t, got, "456")
	})
}

func assertBufferHas(t testing.TB, buf []byte, want string) {
	t.Helper()
	got := string(buf)
	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}
```

- أنشئ `io.Reader` من سلسلة نصية فيها بعض البيانات
- مصفوفة بايتات نقرأ إليها، أصغر من محتويات القارئ
- استدعِ القراءة، وتحقق من المحتويات، وكرر.

من هنا يمكننا أن نتخيل إرسال نوع من إشارات الإلغاء قبل القراءة الثانية لتغيير السلوك.

والآن بعد أن رأينا كيف يعمل، سنبني بقية الوظائف بـ`TDD`.

## اكتب الاختبار أولاً

نريد أن نستطيع تركيب `io.Reader` مع `context.Context`.

مع `TDD` من الأفضل أن تبدأ بتخيل الواجهة البرمجية التي تريدها، وتكتب اختباراً (test) لها.

ومن هناك دع المصرِّف (compiler) ومخرجات الاختبار الفاشل ترشدنا إلى الحل

```go
t.Run("behaves like a normal reader", func(t *testing.T) {
	rdr := NewCancellableReader(strings.NewReader("123456"))
	got := make([]byte, 3)
	_, err := rdr.Read(got)

	if err != nil {
		t.Fatal(err)
	}

	assertBufferHas(t, got, "123")

	_, err = rdr.Read(got)

	if err != nil {
		t.Fatal(err)
	}

	assertBufferHas(t, got, "456")
})
```

## حاول تشغيل الاختبار

```
./cancel_readers_test.go:12:10: undefined: NewCancellableReader
```
## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

سنحتاج إلى تعريف هذه الدالة، وينبغي أن تعيد `io.Reader`

```go
func NewCancellableReader(rdr io.Reader) io.Reader {
	return nil
}
```

إن حاولت تشغيله

```
=== RUN   TestCancelReaders
=== RUN   TestCancelReaders/behaves_like_a_normal_reader
panic: runtime error: invalid memory address or nil pointer dereference [recovered]
	panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x10f8fb5]
```

كما هو متوقع

## اكتب ما يكفي من الشيفرة لينجح الاختبار

في الوقت الحالي، سنعيد فقط `io.Reader` الذي نمرره

```go
func NewCancellableReader(rdr io.Reader) io.Reader {
	return rdr
}
```

ينبغي أن ينجح الاختبار الآن.

أعرف، أعرف، يبدو هذا سخيفاً ومتحذلقاً، لكن قبل الاندفاع إلى العمل المتقن من المهم أن يكون لدينا _بعض_ التحقق من أننا لم نُفسد السلوك "العادي" لـ`io.Reader`، وسيمنحنا هذا الاختبار الثقة ونحن نمضي قدماً.

## اكتب الاختبار أولاً

علينا بعد ذلك محاولة الإلغاء.

```go
t.Run("stops reading when cancelled", func(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	rdr := NewCancellableReader(ctx, strings.NewReader("123456"))
	got := make([]byte, 3)
	_, err := rdr.Read(got)

	if err != nil {
		t.Fatal(err)
	}

	assertBufferHas(t, got, "123")

	cancel()

	n, err := rdr.Read(got)

	if err == nil {
		t.Error("expected an error after cancellation but didn't get one")
	}

	if n > 0 {
		t.Errorf("expected 0 bytes to be read after cancellation but %d were read", n)
	}
})
```

يمكننا نسخ الاختبار الأول تقريباً، لكننا الآن:
- ننشئ `context.Context` مع إمكانية الإلغاء، كي نستطيع الإلغاء بـ`cancel` بعد القراءة الأولى
- ولكي تعمل شيفرتنا (code) سنحتاج إلى تمرير `ctx` إلى دالتنا
- ثم نؤكد أنه لم يُقرأ أي شيء بعد `cancel`

## حاول تشغيل الاختبار

```
./cancel_readers_test.go:33:30: too many arguments in call to NewCancellableReader
	have (context.Context, *strings.Reader)
	want (io.Reader)
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

يخبرنا المصرِّف بما علينا فعله؛ حدّث توقيعنا ليقبل سياقاً

```go
func NewCancellableReader(ctx context.Context, rdr io.Reader) io.Reader {
	return rdr
}
```

(ستحتاج إلى تحديث الاختبار الأول ليمرر `context.Background` أيضاً)

ينبغي أن ترى الآن مخرجات اختبار فاشل واضحة جداً

```
=== RUN   TestCancelReaders
=== RUN   TestCancelReaders/stops_reading_when_cancelled
--- FAIL: TestCancelReaders (0.00s)
    --- FAIL: TestCancelReaders/stops_reading_when_cancelled (0.00s)
        cancel_readers_test.go:48: expected an error but didn't get one
        cancel_readers_test.go:52: expected 0 bytes to be read after cancellation but 3 were read
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

في هذه المرحلة، الأمر نسخ ولصق من التدوينة الأصلية لمات وديفيد، لكننا سنمضي ببطء وتكرارية مع ذلك.

نعرف أننا نحتاج إلى نوع (type) يغلّف `io.Reader` الذي نقرأ منه و`context.Context`، فلننشئه ونحاول إعادته من دالتنا بدلاً من `io.Reader` الأصلي

```go
func NewCancellableReader(ctx context.Context, rdr io.Reader) io.Reader {
	return &readerCtx{
		ctx:      ctx,
		delegate: rdr,
	}
}

type readerCtx struct {
	ctx      context.Context
	delegate io.Reader
}
```

كما شددت مرات كثيرة في هذا الكتاب، امضِ ببطء ودع المصرِّف يساعدك

```
./cancel_readers_test.go:60:3: cannot use &readerCtx literal (type *readerCtx) as type io.Reader in return argument:
	*readerCtx does not implement io.Reader (missing Read method)
```

يبدو التجريد صحيحاً، لكنه لا يحقق الواجهة التي نحتاج إليها (`io.Reader`)، فلنُضِف الطريقة.

```go
func (r *readerCtx) Read(p []byte) (n int, err error) {
	panic("implement me")
}
```

شغّل الاختبارات، وينبغي أن _تُصرَّف_ لكنها تُطلق الذعر. وما زال هذا تقدماً.

لنجعل الاختبار الأول ينجح بمجرد _تفويض_ الاستدعاء إلى `io.Reader` الأساسي

```go
func (r readerCtx) Read(p []byte) (n int, err error) {
	return r.delegate.Read(p)
}
```

في هذه المرحلة صار اختبار المسار الناجح ينجح مجدداً، ويبدو أن لدينا تجريداً جيداً

ولجعل اختبارنا الثاني ينجح، علينا التحقق من `context.Context` لنرى إن كان قد أُلغي.

```go
func (r readerCtx) Read(p []byte) (n int, err error) {
	if err := r.ctx.Err(); err != nil {
		return 0, err
	}
	return r.delegate.Read(p)
}
```

ينبغي أن تنجح كل الاختبارات الآن. وستلاحظ كيف نعيد الخطأ (error) من `context.Context`. وهذا يتيح لمستدعي الشيفرة فحص الأسباب المختلفة التي حدث الإلغاء بسببها، وهذا مشروح أكثر في التدوينة الأصلية.

## الخلاصة

- الواجهات الصغيرة جيدة وسهلة التركيب
- حين تحاول تعزيز شيء ما (مثل `io.Reader`) بشيء آخر، فعادةً ستلجأ إلى [نمط التفويض](https://en.wikipedia.org/wiki/Delegation_pattern)

> في هندسة البرمجيات، نمط التفويض نمط تصميم كائني التوجه يتيح لتركيب الكائنات تحقيق إعادة استعمال الشيفرة نفسها التي يحققها الوراثة.

- من الطرق السهلة لبدء هذا النوع من العمل أن تغلّف المفوَّض إليه، وتكتب اختباراً يؤكد أنه يتصرف كما يتصرف المفوَّض إليه عادةً، قبل أن تبدأ بتركيب أجزاء أخرى لتغيير السلوك. فهذا سيساعدك على إبقاء الأشياء تعمل بشكل صحيح وأنت تكتب الشيفرة نحو هدفك
