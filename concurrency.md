# التزامن

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/concurrency)**

إليك الوضع: كتب أحد زملائك دالة (function) باسم `CheckWebsites`
تتحقق من حالة عناوين URL في قائمة.

```go
package concurrency

type WebsiteChecker func(string) bool

func CheckWebsites(wc WebsiteChecker, urls []string) map[string]bool {
	results := make(map[string]bool)

	for _, url := range urls {
		results[url] = wc(url)
	}

	return results
}
```

تعيد الدالة خريطة (map) تربط كل عنوان URL جرى التحقق منه بقيمة منطقية: `true` للاستجابة
الجيدة، و`false` للاستجابة السيئة.

وعليك أيضاً أن تمرر `WebsiteChecker` يأخذ عنوان URL واحداً ويعيد
قيمة منطقية، وتستعمله الدالة للتحقق من كل المواقع.

أتاح [حقن التبعية][DI] لزميلك أن يختبر الدالة دون
إجراء استدعاءات HTTP حقيقية، مما جعلها موثوقة وسريعة.

إليك الاختبار (test) الذي كتبه:

```go
package concurrency

import (
	"reflect"
	"testing"
)

func mockWebsiteChecker(url string) bool {
	return url != "waat://furhurterwe.geds"
}

func TestCheckWebsites(t *testing.T) {
	websites := []string{
		"http://google.com",
		"http://blog.gypsydave5.com",
		"waat://furhurterwe.geds",
	}

	want := map[string]bool{
		"http://google.com":          true,
		"http://blog.gypsydave5.com": true,
		"waat://furhurterwe.geds":    false,
	}

	got := CheckWebsites(mockWebsiteChecker, websites)

	if !reflect.DeepEqual(want, got) {
		t.Fatalf("wanted %v, got %v", want, got)
	}
}
```

الدالة قيد الإنتاج وتُستعمل للتحقق من مئات المواقع. لكن
زميلك بدأ يتلقى شكاوى من أنها بطيئة، فطلب منك
المساعدة في تسريعها.

## اكتب اختباراً

لنستعمل قياس أداء (benchmark) لاختبار سرعة `CheckWebsites` كي نرى
أثر تغييراتنا.

```go
package concurrency

import (
	"testing"
	"time"
)

func slowStubWebsiteChecker(_ string) bool {
	time.Sleep(20 * time.Millisecond)
	return true
}

func BenchmarkCheckWebsites(b *testing.B) {
	urls := make([]string, 100)
	for i := 0; i < len(urls); i++ {
		urls[i] = "a url"
	}

	for b.Loop() {
		CheckWebsites(slowStubWebsiteChecker, urls)
	}
}
```

يختبر قياس الأداء الدالة `CheckWebsites` باستعمال شريحة (slice) من مئة عنوان URL، ويستعمل
تنفيذاً مزيفاً جديداً لـ`WebsiteChecker`. والدالة `slowStubWebsiteChecker`
بطيئة عمداً، إذ تستعمل `time.Sleep` لتنتظر عشرين ميلي ثانية بالضبط
ثم تعيد `true`.


حين نشغّل قياس الأداء بالأمر `go test -bench=.` (أو `go test -bench="."` إن كنت تستعمل Windows Powershell):

```sh
pkg: github.com/gypsydave5/learn-go-with-tests/concurrency/v0
BenchmarkCheckWebsites-4               1        2249228637 ns/op
PASS
ok      github.com/gypsydave5/learn-go-with-tests/concurrency/v0        2.268s
```

قيس أداء `CheckWebsites` بـ2249228637 نانوثانية، أي نحو ثانيتين
وربع الثانية.

لنحاول جعلها أسرع.

### اكتب ما يكفي من الشيفرة لينجح الاختبار

يمكننا الآن أخيراً أن نتحدث عن التزامن (concurrency)، الذي يعني لأغراض ما
يلي "وجود أكثر من شيء واحد قيد التنفيذ". وهذا أمر
نفعله بشكل طبيعي كل يوم.

على سبيل المثال، أعددت هذا الصباح كوباً من الشاي. وضعت الغلاية على النار، ثم
وبينما كنت أنتظر أن يغلي الماء، أخرجت الحليب من الثلاجة، وأخرجت
الشاي من الخزانة، ووجدت كوبي المفضل، ووضعت كيس الشاي في الكوب،
ثم حين غلى الماء، صببته في الكوب.

ما _لم_ أفعله هو أن أضع الغلاية على النار ثم أقف أحدّق فيها
بشرود حتى يغلي الماء، ثم أفعل كل شيء آخر بعد ذلك.

إن استطعت أن تفهم لماذا إعداد الشاي بالطريقة الأولى أسرع، فستفهم
كيف سنجعل `CheckWebsites` أسرع. فبدلاً من انتظار
استجابة موقع ما قبل إرسال طلب إلى الموقع التالي، سنطلب من
حاسوبنا أن يرسل الطلب التالي أثناء انتظاره.

عادةً في غو (Go)، حين نستدعي دالة `doSomething()` فإننا ننتظر حتى تعود
(حتى لو لم تكن لديها قيمة تعيدها، فإننا ننتظر حتى تنتهي). ونقول إن
هذه العملية *حاجبة*، أي أنها تجعلنا ننتظر حتى تنتهي. أما العملية
التي لا تحجب في غو فتعمل في *عملية* (process) منفصلة تسمى *`goroutine`*.
تخيّل العملية على أنها قراءة صفحة شيفرة (code) غو من الأعلى إلى الأسفل، مع الدخول
إلى "داخل" كل دالة حين تُستدعى لقراءة ما تفعله. وحين تبدأ
عملية منفصلة، فكأن قارئاً آخر بدأ القراءة داخل الدالة،
تاركاً القارئ الأصلي يواصل النزول في الصفحة.

لنطلب من غو بدء `goroutine` جديدة، نحوّل استدعاء الدالة إلى تعليمة `go`
بوضع الكلمة المحجوزة `go` أمامه: `go doSomething()`.

```go
package concurrency

type WebsiteChecker func(string) bool

func CheckWebsites(wc WebsiteChecker, urls []string) map[string]bool {
	results := make(map[string]bool)

	for _, url := range urls {
		go func() {
			results[url] = wc(url)
		}()
	}

	return results
}
```

ولأن الطريقة الوحيدة لبدء `goroutine` هي وضع `go` أمام استدعاء
دالة، فإننا كثيراً ما نستعمل *الدوال المجهولة* حين نريد بدء `goroutine`. وتبدو
الدالة المجهولة الحرفية تماماً مثل التصريح العادي عن دالة،
لكن دون اسم (وهذا غير مفاجئ). ويمكنك أن ترى واحدة منها أعلاه في جسم
حلقة (loop) `for`.

للدوال المجهولة عدد من الميزات التي تجعلها مفيدة، ونستعمل اثنتين
منها أعلاه. أولاً، يمكن تنفيذها في اللحظة نفسها التي
يُصرَّح عنها فيها، وهذا ما تفعله `()` في نهاية الدالة المجهولة.
وثانياً، تحتفظ بالوصول إلى النطاق المعجمي الذي
عُرّفت فيه، فكل المتغيرات (variables) المتاحة في اللحظة التي تصرّح فيها عن
الدالة المجهولة متاحة أيضاً في جسمها.

جسم الدالة المجهولة أعلاه هو نفسه جسم الحلقة
سابقاً. والفرق الوحيد أن كل تكرار (iteration) للحلقة سيبدأ
`goroutine` جديدة، متزامنة مع العملية الحالية (الدالة `WebsiteChecker`).
وستضيف كل `goroutine` نتيجتها إلى خريطة النتائج.

لكن حين نشغّل `go test`:

```sh
--- FAIL: TestCheckWebsites (0.00s)
        CheckWebsites_test.go:31: Wanted map[http://google.com:true http://blog.gypsydave5.com:true waat://furhurterwe.geds:false], got map[]
FAIL
exit status 1
FAIL    github.com/gypsydave5/learn-go-with-tests/concurrency/v1        0.010s

```

### استطراد سريع إلى عالم التزامن...

قد لا تحصل على هذه النتيجة، بل قد تحصل على رسالة ذعر (panic)
سنتحدث عنها بعد قليل. لا تقلق إن حصلت عليها، فقط واصل
تشغيل الاختبار حتى تحصل _فعلاً_ على النتيجة أعلاه، أو تظاهر بأنك حصلت عليها.
الأمر يعود إليك. مرحباً بك في التزامن: حين لا يُعالَج بشكل صحيح يصعب
التنبؤ بما سيحدث. لا تقلق، فلهذا نكتب الاختبارات، لتساعدنا
على معرفة متى نعالج التزامن بطريقة يمكن التنبؤ بها.

### ... وها قد عدنا.

أوقعنا الاختبار الأصلي لـ`CheckWebsites`، فهي تعيد الآن
خريطة فارغة. ما الخطأ الذي حدث؟

لم يكن لدى أي من الـ`goroutines` التي بدأتها حلقة `for` وقت كافٍ لإضافة
نتيجتها إلى الخريطة `results`؛ فالدالة `CheckWebsites` أسرع منها،
وتعيد الخريطة وهي ما زالت فارغة.

لإصلاح ذلك يمكننا ببساطة أن ننتظر ريثما تنهي كل الـ`goroutines` عملها، ثم
نعيد النتيجة. ثانيتان ينبغي أن تكفيا، أليس كذلك؟

```go
package concurrency

import "time"

type WebsiteChecker func(string) bool

func CheckWebsites(wc WebsiteChecker, urls []string) map[string]bool {
	results := make(map[string]bool)

	for _, url := range urls {
		go func() {
			results[url] = wc(url)
		}()
	}

	time.Sleep(2 * time.Second)

	return results
}
```

والآن إن كنت محظوظاً فستحصل على:

```sh
PASS
ok      github.com/gypsydave5/learn-go-with-tests/concurrency/v1        2.012s
```

لكن إن لم تكن محظوظاً (وهذا أرجح إن شغّلتها مع قياس الأداء، لأنك ستحصل على محاولات أكثر)

```sh
fatal error: concurrent map writes

goroutine 8 [running]:
runtime.throw(0x12c5895, 0x15)
        /usr/local/Cellar/go/1.9.3/libexec/src/runtime/panic.go:605 +0x95 fp=0xc420037700 sp=0xc4200376e0 pc=0x102d395
runtime.mapassign_faststr(0x1271d80, 0xc42007acf0, 0x12c6634, 0x17, 0x0)
        /usr/local/Cellar/go/1.9.3/libexec/src/runtime/hashmap_fast.go:783 +0x4f5 fp=0xc420037780 sp=0xc420037700 pc=0x100eb65
github.com/gypsydave5/learn-go-with-tests/concurrency/v3.WebsiteChecker.func1(0xc42007acf0, 0x12d3938, 0x12c6634, 0x17)
        /Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker.go:12 +0x71 fp=0xc4200377c0 sp=0xc420037780 pc=0x12308f1
runtime.goexit()
        /usr/local/Cellar/go/1.9.3/libexec/src/runtime/asm_amd64.s:2337 +0x1 fp=0xc4200377c8 sp=0xc4200377c0 pc=0x105cf01
created by github.com/gypsydave5/learn-go-with-tests/concurrency/v3.WebsiteChecker
        /Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker.go:11 +0xa1

        ... many more scary lines of text ...
```

هذا طويل ومخيف، لكن كل ما علينا فعله هو أن نأخذ نفساً عميقاً ونقرأ
تتبّع المكدس: `fatal error: concurrent map writes`. فأحياناً حين نشغّل
اختباراتنا، تكتب اثنتان من الـ`goroutines` إلى خريطة النتائج في اللحظة نفسها تماماً.
والخرائط في غو لا تحب أن يحاول أكثر من طرف الكتابة إليها في
آن واحد، فيحدث `fatal error`.

هذا _تسابق بيانات_ (data race)، وهو خطأ برمجي يحدث حين تصل اثنتان أو أكثر من الـ`goroutines` إلى موضع الذاكرة نفسه بالتزامن، ويكون أحد هذه الوصولات على الأقل عملية كتابة. ولأننا لا نستطيع التحكم بالضبط بلحظة تنفيذ كل `goroutine`، فنحن معرّضون لأن تحاول عدة `goroutines` الكتابة إلى الخريطة `results` في اللحظة نفسها بالضبط. والخرائط في غو ليست آمنة للكتابة المتزامنة، لذا يطلق وقت التشغيل خطأً قاتلاً لمنع تلف الذاكرة.

تستطيع غو مساعدتنا على اكتشاف حالات التسابق بـ[_كاشف التسابق_][godoc_race_detector] المدمج فيها.
ولتفعيل هذه الميزة، شغّل الاختبارات مع الراية `race`: `go test -race`.

ينبغي أن تحصل على مخرجات تبدو هكذا:

```sh
==================
WARNING: DATA RACE
Write at 0x00c420084d20 by goroutine 8:
  runtime.mapassign_faststr()
      /usr/local/Cellar/go/1.9.3/libexec/src/runtime/hashmap_fast.go:774 +0x0
  github.com/gypsydave5/learn-go-with-tests/concurrency/v3.WebsiteChecker.func1()
      /Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker.go:12 +0x82

Previous write at 0x00c420084d20 by goroutine 7:
  runtime.mapassign_faststr()
      /usr/local/Cellar/go/1.9.3/libexec/src/runtime/hashmap_fast.go:774 +0x0
  github.com/gypsydave5/learn-go-with-tests/concurrency/v3.WebsiteChecker.func1()
      /Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker.go:12 +0x82

Goroutine 8 (running) created at:
  github.com/gypsydave5/learn-go-with-tests/concurrency/v3.WebsiteChecker()
      /Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker.go:11 +0xc4
  github.com/gypsydave5/learn-go-with-tests/concurrency/v3.TestWebsiteChecker()
      /Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker_test.go:27 +0xad
  testing.tRunner()
      /usr/local/Cellar/go/1.9.3/libexec/src/testing/testing.go:746 +0x16c

Goroutine 7 (finished) created at:
  github.com/gypsydave5/learn-go-with-tests/concurrency/v3.WebsiteChecker()
      /Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker.go:11 +0xc4
  github.com/gypsydave5/learn-go-with-tests/concurrency/v3.TestWebsiteChecker()
      /Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker_test.go:27 +0xad
  testing.tRunner()
      /usr/local/Cellar/go/1.9.3/libexec/src/testing/testing.go:746 +0x16c
==================
```

التفاصيل مرة أخرى صعبة القراءة، لكن `WARNING: DATA RACE` واضحة
تماماً. وبقراءة متن الخطأ نرى اثنتين مختلفتين من
الـ`goroutines` تكتبان إلى خريطة:

`Write at 0x00c420084d20 by goroutine 8:`

تكتب إلى كتلة الذاكرة نفسها التي تكتب إليها

`Previous write at 0x00c420084d20 by goroutine 7:`

وفوق ذلك، نرى سطر الشيفرة الذي تحدث فيه الكتابة:

`/Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker.go:12`

وسطر الشيفرة الذي تبدأ فيه الـ`goroutines` رقم 7 و8:

`/Users/gypsydave5/go/src/github.com/gypsydave5/learn-go-with-tests/concurrency/v3/websiteChecker.go:11`

كل ما تحتاج إلى معرفته مطبوع في الطرفية، وكل ما عليك هو
أن تتحلى بالصبر الكافي لقراءته.

### القنوات

يمكننا حل تسابق البيانات هذا بتنسيق الـ`goroutines` باستعمال _القنوات_ (channels).
والقنوات هيكل بيانات في غو يمكنه استقبال القيم وإرسالها. وهذه
العمليات، مع تفاصيلها، تتيح التواصل بين العمليات
المختلفة.

نريد في هذه الحالة أن نفكر في التواصل بين العملية الأم
وكل `goroutine` تنشئها لتنفيذ عمل تشغيل الدالة
`WebsiteChecker` على عنوان URL الخاص بها.

```go
package concurrency

type WebsiteChecker func(string) bool
type result struct {
	string
	bool
}

func CheckWebsites(wc WebsiteChecker, urls []string) map[string]bool {
	results := make(map[string]bool)
	resultChannel := make(chan result)

	for _, url := range urls {
		go func() {
			resultChannel <- result{url, wc(url)}
		}()
	}

	for i := 0; i < len(urls); i++ {
		r := <-resultChannel
		results[r.string] = r.bool
	}

	return results
}
```

> **ملاحظة حول `url` داخل الـ`goroutine`.** كل دورة من دورات الحلقة تبدأ `goroutine` جديدة تشير إلى `url`، دون تمريره إليها صراحةً. ومنذ غو 1.22 صار هذا آمناً: فقد عُدّلت مواصفة اللغة بحيث يكون `url` متغيراً جديداً في كل دورة، فتلتقط كل `goroutine` نسختها الخاصة.
>
> أما إن شغّلت هذا في مشروع يصرّح ملف `go.mod` فيه بإصدار `go` *أقدم* من `1.22`، فستحصل على السلوك القديم بدلاً من ذلك: يكون `url` متغيراً واحداً تتشاركه كل الدورات وتعيد استعماله، فحين تعمل الـ`goroutines` سترى على الأرجح كلها القيمة نفسها لـ`url` (وهي غالباً القيمة الأخيرة). وهذا يوقع الناس في الخطأ لأن *سلسلة أدوات* غو لديك قد تكون حديثة بينما يكون الموجّه `go` في ملف `go.mod` قديماً، وسلسلة الأدوات تلتزم بدلالات متغير الحلقة التي يقتضيها الإصدار المصرَّح عنه. والحل في ملف `go.mod` قديم هو تمرير `url` إلى الـ`goroutine` صراحةً: `go func(url string) { ... }(url)`.

إلى جانب الخريطة `results` لدينا الآن `resultChannel`، ننشئها بـ`make` بالطريقة
نفسها. و`chan result` هو نوع القناة، أي قناة من القيم `result`.
وقد أنشئ النوع الجديد `result` لربط القيمة المعادة من
`WebsiteChecker` بعنوان URL الذي يجري التحقق منه، فهو بنية (struct) من `string` و
`bool`. وبما أننا لا نحتاج إلى تسمية أي من القيمتين، فكل منهما مجهولة
داخل البنية؛ وقد يكون هذا مفيداً حين يصعب معرفة الاسم المناسب
لقيمة ما.

والآن حين نمر على عناوين URL، فبدلاً من الكتابة إلى `map` مباشرة،
نرسل بنية `result` لكل استدعاء لـ`wc` إلى `resultChannel`
بـ_تعليمة إرسال_. وهي تستعمل العامل `<-`، مع القناة على
اليسار والقيمة على اليمين:

```go
// Send statement
resultChannel <- result{url, wc(url)}
```

تمر حلقة `for` التالية مرة واحدة على كل عنوان URL. ونستعمل داخلها
_تعبير استقبال_، يسند قيمة مستقبَلة من قناة إلى
متغير. وهو يستعمل أيضاً العامل `<-`، لكن مع عكس الطرفين:
القناة الآن على اليمين، والمتغير الذي
نسند إليه على اليسار:

```go
// Receive expression
r := <-resultChannel
```

ثم نستعمل النتيجة `result` المستقبَلة لتحديث الخريطة.

بإرسال النتائج إلى قناة، نستطيع التحكم بتوقيت كل كتابة
إلى خريطة النتائج، فنضمن أنها تحدث واحدة تلو الأخرى. ومع أن كل
استدعاء لـ`wc`، وكل إرسال إلى قناة النتائج، يحدث بشكل متزامن
داخل عمليته الخاصة، فإن كل نتيجة تُعالَج واحدة تلو الأخرى
ونحن نأخذ القيم من قناة النتائج بتعبير الاستقبال.

استعملنا التزامن للجزء من الشيفرة الذي أردنا تسريعه، مع
الحرص على أن يظل الجزء الذي لا يمكن أن يحدث في آن واحد يحدث بشكل خطي.
وتواصلنا بين العمليات المتعددة المعنية باستعمال
القنوات.

حين نشغّل قياس الأداء:

```sh
pkg: github.com/gypsydave5/learn-go-with-tests/concurrency/v2
BenchmarkCheckWebsites-8             100          23406615 ns/op
PASS
ok      github.com/gypsydave5/learn-go-with-tests/concurrency/v2        2.377s
```
23406615 نانوثانية، أي 0.023 ثانية، وهذا أسرع بنحو مئة مرة من
الدالة الأصلية. نجاح باهر.

## الخلاصة

كان نصيب `TDD` في هذا التمرين أقل قليلاً من المعتاد. فقد كنا بمعنى ما
نشارك في عملية إعادة هيكلة (refactoring) طويلة واحدة للدالة `CheckWebsites`؛ فالمدخلات
والمخرجات لم تتغير قط، بل صارت أسرع فقط. لكن الاختبارات التي كانت
لدينا، إضافة إلى قياس الأداء الذي كتبناه، أتاحت لنا إعادة هيكلة `CheckWebsites`
بطريقة حافظت على الثقة بأن البرنامج ما زال يعمل، مع
إثبات أنه صار أسرع فعلاً.

وتعلّمنا أثناء تسريعها عن

- الـ*`goroutines`*، وهي الوحدة الأساسية للتزامن في غو، وتتيح لنا إدارة أكثر
  من طلب للتحقق من المواقع.
- *الدوال المجهولة*، التي استعملناها لبدء كل عملية من العمليات المتزامنة
  التي تتحقق من المواقع.
- *القنوات*، للمساعدة على تنظيم التواصل بين العمليات
  المختلفة والتحكم به، مما أتاح لنا تجنب خطأ *التسابق*.
- *كاشف التسابق* الذي ساعدنا على تنقيح المشكلات في الشيفرة المتزامنة

### اجعلها سريعة

إحدى صيغ الطريقة الرشيقة في بناء البرمجيات، والتي كثيراً ما تُنسب خطأً إلى كينت
بيك، هي:

> [اجعلها تعمل، اجعلها صحيحة، اجعلها سريعة][wrf]

حيث "تعمل" تعني جعل الاختبارات تنجح، و"صحيحة" تعني إعادة هيكلة الشيفرة، و
"سريعة" تعني تحسين الشيفرة لجعلها، مثلاً، تعمل بسرعة. ولا يمكننا
"جعلها سريعة" إلا بعد أن نجعلها تعمل ونجعلها صحيحة. وقد كنا محظوظين بأن
الشيفرة التي أُعطيت لنا كانت مثبتة العمل أصلاً، ولم تحتج إلى
إعادة هيكلة. ولا ينبغي أبداً أن نحاول "جعلها سريعة" قبل تنفيذ
الخطوتين الأخريين، لأن

> [التحسين المبكر أصل كل الشرور][popt]
> -- دونالد كنوث

[DI]: dependency-injection.md
[wrf]: http://wiki.c2.com/?MakeItWorkMakeItRightMakeItFast
[godoc_race_detector]: https://blog.golang.org/race-detector
[popt]: http://wiki.c2.com/?PrematureOptimization
