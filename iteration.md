# التكرار

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/for)**

لتنفيذ الأشياء بشكل متكرر في غو (Go)، تحتاج إلى `for`. فليس في غو كلمات محجوزة مثل `while` أو `do` أو `until`، ولا يمكنك أن تستعمل إلا `for`. وهذا أمر جيد!

لنكتب اختباراً (test) لدالة (function) تكرر حرفاً 5 مرات.

لا جديد حتى الآن، فحاول أن تكتبه بنفسك للتمرّن.

## اكتب الاختبار أولاً

```go
package iteration

import "testing"

func TestRepeat(t *testing.T) {
	repeated := Repeat("a")
	expected := "aaaaa"

	if repeated != expected {
		t.Errorf("expected %q but got %q", expected, repeated)
	}
}
```

## حاول تشغيل الاختبار

`./repeat_test.go:6:14: undefined: Repeat`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

_حافظ على الانضباط!_ لا تحتاج الآن إلى معرفة أي شيء جديد لجعل الاختبار يفشل كما ينبغي.

كل ما عليك فعله الآن هو ما يكفي لجعله يُصرَّف كي تتحقق من أن اختبارك مكتوب جيداً.

```go
package iteration

func Repeat(character string) string {
	return ""
}
```

أليس من الجميل أن تعرف أنك تعرف من غو ما يكفي لكتابة اختبارات لبعض المشكلات الأساسية؟ وهذا يعني أنك تستطيع الآن أن تجرّب في شيفرة (code) الإنتاج قدر ما تشاء، وأنت تعرف أنها تتصرف كما تأمل.

`repeat_test.go:10: expected 'aaaaa' but got ''`

## اكتب ما يكفي من الشيفرة لينجح الاختبار

صياغة `for` عادية جداً وتتبع معظم اللغات الشبيهة بلغة C في ذلك.

```go
func Repeat(character string) string {
	var repeated string
	for i := 0; i < 5; i++ {
		repeated = repeated + character
	}
	return repeated
}
```

على خلاف لغات أخرى مثل C وJava وJavaScript، لا توجد أقواس حول المكونات الثلاثة لتعليمة `for`، والأقواس المعقوصة `{ }` مطلوبة دائماً. لعلك تتساءل عما يحدث في السطر

```go
	var repeated string
```

إذ إننا نستعمل `:=` حتى الآن للتصريح عن المتغيرات (variables) وتهيئتها. لكن `:=` ليس إلا [اختصاراً للخطوتين معاً](https://gobyexample.com/variables). وهنا نصرّح فقط عن متغير من النوع `string`، ولذلك استعملنا الصيغة الصريحة. ويمكننا أيضاً استعمال `var` للتصريح عن الدوال، كما سنرى لاحقاً.

شغّل الاختبار، وينبغي أن ينجح.

الأشكال الأخرى لحلقة (loop) `for` موصوفة [هنا](https://gobyexample.com/for).

## أعد الهيكلة

حان الآن وقت إعادة الهيكلة (refactor) وتقديم تركيب لغوي آخر، هو عامل الإسناد `+=`.

```go
const repeatCount = 5

func Repeat(character string) string {
	var repeated string
	for i := 0; i < repeatCount; i++ {
		repeated += character
	}
	return repeated
}
```

العامل `+=` يسمى _"عامل الجمع والإسناد"_، وهو يضيف الطرف الأيمن إلى الطرف الأيسر ويسند النتيجة إلى الطرف الأيسر. ويعمل مع أنواع أخرى مثل الأعداد الصحيحة.

### قياس الأداء

كتابة [قياسات الأداء (benchmarks)](https://golang.org/pkg/testing/#hdr-Benchmarks) في غو ميزة أخرى من الدرجة الأولى في اللغة، وهي تشبه كثيراً كتابة الاختبارات.

```go
func BenchmarkRepeat(b *testing.B) {
	for b.Loop() {
		Repeat("a")
	}
}
```

سترى أن الشيفرة تشبه كثيراً الاختبار.

يمنحك `testing.B` الوصول إلى دالة الحلقة. وتعيد `Loop()` القيمة `true` ما دام ينبغي لقياس الأداء أن يستمر في العمل.

حين تُنفَّذ شيفرة قياس الأداء، فإنها تقيس المدة التي تستغرقها. وبعد أن تعيد `Loop()` القيمة `false`، يحتوي `b.N` على العدد الكلي للدورات التي نُفّذت.

لا ينبغي أن يهمك عدد مرات تشغيل الشيفرة، فإطار العمل سيحدد القيمة "الجيدة" لذلك ليعطيك نتائج معقولة.

لتشغيل قياسات الأداء، نفّذ `go test -bench=.` (أو `go test -bench="."` إن كنت تستعمل Windows Powershell)

```text
goos: darwin
goarch: amd64
pkg: github.com/quii/learn-go-with-tests/for/v4
10000000           136 ns/op
PASS
```

معنى `136 ns/op` أن دالتنا تستغرق في المتوسط 136 نانوثانية لتعمل (على حاسوبي). وهذا جيد إلى حد كبير! ولاختبار ذلك شغّلها 10000000 مرة.

**ملاحظة:** تُشغَّل قياسات الأداء افتراضياً بشكل تسلسلي.

لا يُقاس إلا زمن جسم الحلقة؛ إذ تُستثنى شيفرة التهيئة والتنظيف تلقائياً من توقيت قياس الأداء. ويكون قياس الأداء النموذجي على هذا الشكل:

```go
func Benchmark(b *testing.B) {
	//... setup ...
	for b.Loop() {
		//... code to measure ...
	}
	//... cleanup ...
}
```

السلاسل النصية في غو غير قابلة للتغيير (immutable)، أي أن كل عملية ضم، كتلك التي في دالتنا `Repeat`، تتضمن نسخ الذاكرة لاستيعاب السلسلة الجديدة. وهذا يؤثر في الأداء، خصوصاً عند ضم السلاسل بكثافة.

توفر المكتبة القياسية النوع `strings.Builder`[stringsBuilder] الذي يقلّل نسخ الذاكرة إلى أدنى حد.
وهو يحقق الطريقة `WriteString` التي نستطيع استعمالها لضم السلاسل:

```go
const repeatCount = 5

func Repeat(character string) string {
	var repeated strings.Builder
	for i := 0; i < repeatCount; i++ {
		repeated.WriteString(character)
	}
	return repeated.String()
}
```

**ملاحظة**: علينا استدعاء الطريقة `String` للحصول على النتيجة النهائية.

نستطيع استعمال `BenchmarkRepeat` للتأكد من أن `strings.Builder` يحسّن الأداء تحسيناً ملحوظاً.
شغّل `go test -bench=. -benchmem`:

```text
goos: darwin
goarch: amd64
pkg: github.com/quii/learn-go-with-tests/for/v4
10000000           25.70 ns/op           8 B/op           1 allocs/op
PASS
```

تعرض الراية `-benchmem` معلومات عن تخصيصات الذاكرة:

* القيمة `B/op`: عدد البايتات المخصصة في كل دورة
* القيمة `allocs/op`: عدد تخصيصات الذاكرة في كل دورة

## تمارين للتدرّب

* غيّر الاختبار بحيث يستطيع المستدعي تحديد عدد مرات تكرار الحرف، ثم أصلح الشيفرة
* اكتب `ExampleRepeat` لتوثيق دالتك
* ألقِ نظرة على الحزمة [strings](https://golang.org/pkg/strings). ابحث عن دوال تظن أنها قد تكون مفيدة، وجرّبها بكتابة اختبارات كما فعلنا هنا. فاستثمار الوقت في تعلّم المكتبة القياسية سيؤتي ثماره مع الوقت.

## الخلاصة

* مزيد من التمرّن على `TDD`
* تعلّمنا `for`
* تعلّمنا كيف نكتب قياسات الأداء

[stringsBuilder]: https://pkg.go.dev/strings#Builder
