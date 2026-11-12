# أنواع الأخطاء

**[تجد كل الشيفرة هنا](https://github.com/quii/learn-go-with-tests/tree/main/q-and-a/error-types)**

**إنشاء أنواعك الخاصة للأخطاء قد يكون وسيلة أنيقة لترتيب شيفرتك، وجعلها أسهل في الاستعمال والاختبار.**

يسأل بيدرو على Gopher Slack

> إن كنت أنشئ خطأً مثل `fmt.Errorf("%s must be foo, got %s", bar, baz)`، فهل هناك طريقة لاختبار المساواة دون مقارنة قيمة السلسلة النصية؟

لنصنع دالة (function) تساعدنا على استكشاف هذه الفكرة.

```go
// DumbGetter will get the string body of url if it gets a 200
func DumbGetter(url string) (string, error) {
	res, err := http.Get(url)

	if err != nil {
		return "", fmt.Errorf("problem fetching from %s, %v", url, err)
	}

	if res.StatusCode != http.StatusOK {
		return "", fmt.Errorf("did not get 200 from %s, got %d", url, res.StatusCode)
	}

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body) // ignoring err for brevity

	return string(body), nil
}
```

ليس من غير المألوف كتابة دالة قد تفشل لأسباب مختلفة، ونريد التأكد من أننا نعالج كل سيناريو بشكل صحيح.

وكما يقول بيدرو، _يمكننا_ كتابة اختبار (test) لخطأ الحالة هكذا.

```go
t.Run("when you don't get a 200 you get a status error", func(t *testing.T) {

	svr := httptest.NewServer(http.HandlerFunc(func(res http.ResponseWriter, req *http.Request) {
		res.WriteHeader(http.StatusTeapot)
	}))
	defer svr.Close()

	_, err := DumbGetter(svr.URL)

	if err == nil {
		t.Fatal("expected an error")
	}

	want := fmt.Sprintf("did not get 200 from %s, got %d", svr.URL, http.StatusTeapot)
	got := err.Error()

	if got != want {
		t.Errorf(`got "%v", want "%v"`, got, want)
	}
})
```

ينشئ هذا الاختبار خادماً يعيد دائماً `StatusTeapot`، ثم نستعمل عنوان URL الخاص به وسيطاً (argument) لـ`DumbGetter`، كي نرى أنه يعالج الاستجابات غير `200` بشكل صحيح.

## مشكلات طريقة الاختبار هذه

يحاول هذا الكتاب التشديد على أن _تصغي إلى اختباراتك_، وهذا الاختبار لا _يبدو_ جيداً:

- نبني السلسلة النصية نفسها التي تبنيها شيفرة الإنتاج لنختبرها
- قراءته وكتابته مزعجتان
- هل السلسلة النصية الدقيقة لرسالة الخطأ هي ما _يهمنا فعلاً_؟

ماذا يخبرنا هذا؟ إن سهولة استعمال اختبارنا ستنعكس على أي شيفرة (code) أخرى تحاول استعمال شيفرتنا.

كيف يتصرف مستخدم شيفرتنا مع الأنواع المحددة من الأخطاء التي نعيدها؟ أفضل ما يستطيع فعله هو النظر في سلسلة الخطأ النصية، وهذا عرضة للأخطاء إلى حد بعيد وفظيع الكتابة.

## ما ينبغي أن نفعله

مع `TDD` نستفيد من الدخول في طريقة التفكير التالية:

> كيف _أريد_ أنا أن أستعمل هذه الشيفرة؟

ما يمكننا فعله لـ`DumbGetter` هو توفير وسيلة للمستخدمين لاستعمال نظام الأنواع لفهم نوع الخطأ الذي حدث.

ماذا لو استطاعت `DumbGetter` أن تعيد لنا شيئاً مثل

```go
type BadStatusError struct {
	URL    string
	Status int
}
```

بدلاً من سلسلة نصية سحرية، صارت لدينا _بيانات_ فعلية نعمل معها.

لنغيّر اختبارنا الحالي ليعكس هذه الحاجة

```go
t.Run("when you don't get a 200 you get a status error", func(t *testing.T) {

	svr := httptest.NewServer(http.HandlerFunc(func(res http.ResponseWriter, req *http.Request) {
		res.WriteHeader(http.StatusTeapot)
	}))
	defer svr.Close()

	_, err := DumbGetter(svr.URL)

	if err == nil {
		t.Fatal("expected an error")
	}

	got, isStatusErr := err.(BadStatusError)

	if !isStatusErr {
		t.Fatalf("was not a BadStatusError, got %T", err)
	}

	want := BadStatusError{URL: svr.URL, Status: http.StatusTeapot}

	if got != want {
		t.Errorf("got %v, want %v", got, want)
	}
})
```

سنضطر إلى جعل `BadStatusError` يحقق واجهة الخطأ.

```go
func (b BadStatusError) Error() string {
	return fmt.Sprintf("did not get 200 from %s, got %d", b.URL, b.Status)
}
```

### ماذا يفعل الاختبار؟

بدلاً من التحقق من السلسلة النصية الدقيقة للخطأ، نجري [توكيد نوع](https://tour.golang.org/methods/15) على الخطأ لنرى إن كان `BadStatusError`. وهذا يعكس رغبتنا في _نوع_ الخطأ بوضوح أكبر. وبافتراض نجاح التوكيد، يمكننا بعد ذلك التحقق من أن خصائص الخطأ صحيحة.

حين نشغّل الاختبار، يخبرنا بأننا لم نُعِد نوع الخطأ الصحيح

```
--- FAIL: TestDumbGetter (0.00s)
    --- FAIL: TestDumbGetter/when_you_dont_get_a_200_you_get_a_status_error (0.00s)
    	error-types_test.go:56: was not a BadStatusError, got *errors.errorString
```

لنصلح `DumbGetter` بتحديث شيفرة معالجة الأخطاء لتستعمل نوعنا

```go
if res.StatusCode != http.StatusOK {
	return "", BadStatusError{URL: url, Status: res.StatusCode}
}
```

كان لهذا التغيير بعض _الآثار الإيجابية الحقيقية_

- صارت الدالة `DumbGetter` أبسط، فلم تعد تهتم بتعقيدات سلسلة الخطأ النصية، بل تنشئ `BadStatusError` فحسب.
- صارت اختباراتنا تعكس (وتوثّق) ما _يمكن_ أن يفعله مستخدم شيفرتنا إن قرر أنه يريد معالجة أخطاء أكثر تطوراً من مجرد التسجيل. فكل ما عليه هو إجراء توكيد نوع، فيحصل على وصول سهل إلى خصائص الخطأ.
- وما زال "مجرد" `error`، لذا إن شاؤوا يستطيعون تمريره إلى أعلى مكدس الاستدعاءات أو تسجيله كأي `error` آخر.

## الخلاصة

إن وجدت نفسك تختبر عدة حالات خطأ، فلا تقع في فخ مقارنة رسائل الخطأ.

فهذا يقود إلى اختبارات متقلبة وصعبة القراءة والكتابة، ويعكس الصعوبات التي سيواجهها مستخدمو شيفرتك إن احتاجوا هم أيضاً إلى فعل أشياء مختلفة بحسب نوع الأخطاء التي حدثت.

تأكد دائماً من أن اختباراتك تعكس الطريقة التي _تحب_ أن تستعمل بها شيفرتك، لذا فكّر في هذا الصدد في إنشاء أنواع أخطاء تغلّف أنواع أخطائك. وهذا يجعل معالجة الأنواع المختلفة من الأخطاء أسهل لمستخدمي شيفرتك، ويجعل كتابة شيفرة معالجة الأخطاء لديك أبسط وأسهل قراءة.

## ملحق

منذ غو (Go) 1.13 صارت هناك طرق جديدة للعمل مع الأخطاء في المكتبة القياسية، يتناولها [مقال في مدونة غو](https://blog.golang.org/go1.13-errors)

```go
t.Run("when you don't get a 200 you get a status error", func(t *testing.T) {

	svr := httptest.NewServer(http.HandlerFunc(func(res http.ResponseWriter, req *http.Request) {
		res.WriteHeader(http.StatusTeapot)
	}))
	defer svr.Close()

	_, err := DumbGetter(svr.URL)

	if err == nil {
		t.Fatal("expected an error")
	}

	var got BadStatusError
	isBadStatusError := errors.As(err, &got)
	want := BadStatusError{URL: svr.URL, Status: http.StatusTeapot}

	if !isBadStatusError {
		t.Fatalf("was not a BadStatusError, got %T", err)
	}

	if got != want {
		t.Errorf("got %v, want %v", got, want)
	}
})
```

نستعمل في هذه الحالة [`errors.As`](https://pkg.go.dev/errors#example-As) لمحاولة استخراج خطئنا إلى نوعنا المخصص. وهي تعيد `bool` للدلالة على النجاح، وتستخرجه إلى `got` لنا.
