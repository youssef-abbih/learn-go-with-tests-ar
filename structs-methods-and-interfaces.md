# البنى والطرق والواجهات

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/structs)**

لنفترض أننا نحتاج إلى شيفرة (code) هندسية تحسب محيط مستطيل بمعلومية ارتفاعه وعرضه. يمكننا كتابة الدالة (function) `Perimeter(width float64, height float64)`، حيث `float64` نوع للأعداد العشرية مثل `123.45`.

ينبغي أن تكون دورة `TDD` مألوفة لك الآن.

## اكتب الاختبار أولاً

```go
func TestPerimeter(t *testing.T) {
	got := Perimeter(10.0, 10.0)
	want := 40.0

	if got != want {
		t.Errorf("got %.2f want %.2f", got, want)
	}
}
```

هل لاحظت سلسلة التنسيق الجديدة؟ الحرف `f` من أجل `float64`، و`.2` تعني طباعة منزلتين عشريتين.

## حاول تشغيل الاختبار

`./shapes_test.go:6:9: undefined: Perimeter`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

```go
func Perimeter(width float64, height float64) float64 {
	return 0
}
```

والنتيجة هي `shapes_test.go:10: got 0.00 want 40.00`.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func Perimeter(width float64, height float64) float64 {
	return 2 * (width + height)
}
```

الأمر سهل حتى الآن. لننشئ الآن دالة باسم `Area(width, height float64)` تعيد مساحة المستطيل.

حاول أن تكتبها بنفسك متبعاً دورة `TDD`.

ينبغي أن تنتهي إلى اختبارات (tests) كهذه

```go
func TestPerimeter(t *testing.T) {
	got := Perimeter(10.0, 10.0)
	want := 40.0

	if got != want {
		t.Errorf("got %.2f want %.2f", got, want)
	}
}

func TestArea(t *testing.T) {
	got := Area(12.0, 6.0)
	want := 72.0

	if got != want {
		t.Errorf("got %.2f want %.2f", got, want)
	}
}
```

وشيفرة كهذه

```go
func Perimeter(width float64, height float64) float64 {
	return 2 * (width + height)
}

func Area(width float64, height float64) float64 {
	return width * height
}
```

## أعد الهيكلة

تؤدي شيفرتنا المهمة، لكنها لا تتضمن أي شيء صريح عن المستطيلات. فقد يحاول مطور غافل أن يمرر عرض مثلث وارتفاعه إلى هذه الدوال دون أن يدرك أنها ستعيد إجابة خاطئة.

يمكننا ببساطة أن نعطي الدوال أسماء أكثر تحديداً مثل `RectangleArea`. لكن الحل الأنظف هو أن نعرّف _نوعاً_ (type) خاصاً بنا باسم `Rectangle` يغلّف هذا المفهوم.

يمكننا إنشاء نوع بسيط باستعمال **بنية** (struct). و[البنية](https://golang.org/ref/spec#Struct_types) ليست إلا مجموعة مسماة من الحقول يمكنك تخزين البيانات فيها.

صرّح عن بنية هكذا

```go
type Rectangle struct {
	Width  float64
	Height float64
}
```

لنعد الآن هيكلة الاختبارات لتستعمل `Rectangle` بدلاً من قيم `float64` المجردة.

```go
func TestPerimeter(t *testing.T) {
	rectangle := Rectangle{10.0, 10.0}
	got := Perimeter(rectangle)
	want := 40.0

	if got != want {
		t.Errorf("got %.2f want %.2f", got, want)
	}
}

func TestArea(t *testing.T) {
	rectangle := Rectangle{12.0, 6.0}
	got := Area(rectangle)
	want := 72.0

	if got != want {
		t.Errorf("got %.2f want %.2f", got, want)
	}
}
```

تذكّر أن تشغّل اختباراتك قبل محاولة الإصلاح. ينبغي أن تُظهر الاختبارات خطأً مفيداً مثل

```text
./shapes_test.go:7:18: not enough arguments in call to Perimeter
    have (Rectangle)
    want (float64, float64)
```

يمكنك الوصول إلى حقول البنية بالصياغة `myStruct.field`.

غيّر الدالتين لإصلاح الاختبار.

```go
func Perimeter(rectangle Rectangle) float64 {
	return 2 * (rectangle.Width + rectangle.Height)
}

func Area(rectangle Rectangle) float64 {
	return rectangle.Width * rectangle.Height
}
```

أرجو أن توافقني على أن تمرير `Rectangle` إلى دالة يعبّر عن قصدنا بوضوح أكبر، لكن لاستعمال البنى فوائد أخرى سنتناولها لاحقاً.

متطلبنا التالي هو كتابة دالة `Area` للدوائر.

## اكتب الاختبار أولاً

```go
func TestArea(t *testing.T) {

	t.Run("rectangles", func(t *testing.T) {
		rectangle := Rectangle{12, 6}
		got := Area(rectangle)
		want := 72.0

		if got != want {
			t.Errorf("got %g want %g", got, want)
		}
	})

	t.Run("circles", func(t *testing.T) {
		circle := Circle{10}
		got := Area(circle)
		want := 314.1592653589793

		if got != want {
			t.Errorf("got %g want %g", got, want)
		}
	})

}
```

كما ترى، استُبدل الحرف `f` بالحرف `g`، ولذلك سبب وجيه.
فاستعمال `g` يطبع عدداً عشرياً أدق في رسالة الخطأ ([خيارات الحزمة fmt](https://golang.org/pkg/fmt/)).
فمثلاً، عند حساب مساحة دائرة نصف قطرها 1.5، يعرض `f` القيمة `7.068583` بينما يعرض `g` القيمة `7.0685834705770345`.

## حاول تشغيل الاختبار

`./shapes_test.go:28:13: undefined: Circle`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

علينا تعريف النوع `Circle`.

```go
type Circle struct {
	Radius float64
}
```

حاول الآن تشغيل الاختبارات مجدداً

`./shapes_test.go:29:14: cannot use circle (type Circle) as type Rectangle in argument to Area`

تسمح لك بعض لغات البرمجة بفعل شيء كهذا:

```go
func Area(circle Circle) float64       {}
func Area(rectangle Rectangle) float64 {}
```

لكن لا يمكنك ذلك في غو (Go)

`./shapes.go:20:32: Area redeclared in this block`

أمامنا خياران:

* يمكن أن تكون لديك دوال بالاسم نفسه مصرّح عنها في _حزم_ (packages) مختلفة. لذا يمكننا إنشاء `Area(Circle)` في حزمة جديدة، لكن هذا يبدو مبالغة هنا.
* يمكننا بدلاً من ذلك تعريف [_طرق_](https://golang.org/ref/spec#Method_declarations) على أنواعنا المعرّفة حديثاً.

### ما الطرق؟

كنا حتى الآن نكتب _دوال_ فقط، لكننا كنا نستعمل بعض الطرق (methods). فحين نستدعي `t.Errorf` فإننا نستدعي الطريقة `Errorf` على نسخة `t` (من النوع `testing.T`).

الطريقة دالة لها مستقبِل.
ويربط التصريح عن الطريقة معرّفاً، هو اسم الطريقة، بطريقة، ويقرن الطريقة بالنوع الأساسي للمستقبِل.

تشبه الطرق الدوال كثيراً، لكنها تُستدعى على نسخة من نوع معيّن. فبينما يمكنك استدعاء الدوال أينما شئت، مثل `Area(rectangle)`، لا يمكنك استدعاء الطرق إلا على "أشياء".

سيساعدنا مثال على الفهم، فلنغيّر اختباراتنا أولاً لتستدعي طرقاً بدلاً من ذلك، ثم نصلح الشيفرة.

```go
func TestArea(t *testing.T) {

	t.Run("rectangles", func(t *testing.T) {
		rectangle := Rectangle{12, 6}
		got := rectangle.Area()
		want := 72.0

		if got != want {
			t.Errorf("got %g want %g", got, want)
		}
	})

	t.Run("circles", func(t *testing.T) {
		circle := Circle{10}
		got := circle.Area()
		want := 314.1592653589793

		if got != want {
			t.Errorf("got %g want %g", got, want)
		}
	})

}
```

إن حاولنا تشغيل الاختبارات، نحصل على

```text
./shapes_test.go:19:19: rectangle.Area undefined (type Rectangle has no field or method Area)
./shapes_test.go:29:16: circle.Area undefined (type Circle has no field or method Area)
```

> type Circle has no field or method Area

أود أن أكرر كم هو رائع المصرِّف (compiler) هنا. من المهم جداً أن تأخذ وقتك في قراءة رسائل الخطأ التي تظهر لك بتمهل، فهذا سيفيدك على المدى الطويل.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

لنُضِف بعض الطرق إلى أنواعنا

```go
type Rectangle struct {
	Width  float64
	Height float64
}

func (r Rectangle) Area() float64 {
	return 0
}

type Circle struct {
	Radius float64
}

func (c Circle) Area() float64 {
	return 0
}
```

صياغة التصريح عن الطرق تكاد تكون مثل صياغة الدوال، وذلك لأنهما متشابهتان جداً. والفرق الوحيد هو صياغة مستقبِل الطريقة `func (receiverName ReceiverType) MethodName(args)`.

حين تُستدعى طريقتك على متغير (variable) من ذلك النوع، تحصل على مرجع إلى بياناته عبر المتغير `receiverName`. وفي كثير من لغات البرمجة الأخرى يحدث هذا ضمنياً، وتصل إلى المستقبِل عبر `this`.

من الأعراف في غو أن يكون اسم متغير المستقبِل هو الحرف الأول من اسم النوع.

```
r Rectangle
```

إن حاولت إعادة تشغيل الاختبارات، فينبغي أن تُصرَّف الآن وتعطيك مخرجات فاشلة.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

لنجعل الآن اختبارات المستطيل تنجح بإصلاح طريقتنا الجديدة

```go
func (r Rectangle) Area() float64 {
	return r.Width * r.Height
}
```

إن أعدت تشغيل الاختبارات، فينبغي أن تنجح اختبارات المستطيل، بينما يظل اختبار الدائرة فاشلاً.

لجعل الدالة `Area` الخاصة بالدائرة تنجح، سنستعير الثابت (constant) `Pi` من الحزمة `math` (تذكّر أن تستوردها).

```go
func (c Circle) Area() float64 {
	return math.Pi * c.Radius * c.Radius
}
```

## أعد الهيكلة

في اختباراتنا شيء من الازدواجية.

كل ما نريده هو أن نأخذ مجموعة من _الأشكال_، ونستدعي عليها الطريقة `Area()`، ثم نتحقق من النتيجة.

نريد أن نستطيع كتابة دالة من نوع ما باسم `checkArea` نمرر إليها قيماً من `Rectangle` و`Circle` معاً، لكنها تفشل في التصريف إن حاولنا تمرير شيء ليس شكلاً.

في غو، يمكننا التعبير عن هذا القصد بـ**الواجهات** (interfaces).

[الواجهات](https://golang.org/ref/spec#Interface_types) مفهوم قوي جداً في اللغات ثابتة الأنواع مثل غو، لأنها تتيح لك إنشاء دوال يمكن استعمالها مع أنواع مختلفة، وكتابة شيفرة منفصلة الأجزاء إلى حد كبير مع الحفاظ على أمان الأنواع.

لنقدّم هذا بإعادة هيكلة اختباراتنا.

```go
func TestArea(t *testing.T) {

	checkArea := func(t testing.TB, shape Shape, want float64) {
		t.Helper()
		got := shape.Area()
		if got != want {
			t.Errorf("got %g want %g", got, want)
		}
	}

	t.Run("rectangles", func(t *testing.T) {
		rectangle := Rectangle{12, 6}
		checkArea(t, rectangle, 72.0)
	})

	t.Run("circles", func(t *testing.T) {
		circle := Circle{10}
		checkArea(t, circle, 314.1592653589793)
	})

}
```

ننشئ دالة مساعدة كما فعلنا في تمارين أخرى، لكننا نطلب هذه المرة تمرير قيمة من النوع `Shape`. فإن حاولنا استدعاءها بشيء ليس شكلاً، فلن يتم التصريف.

كيف يصبح شيء ما شكلاً؟ نخبر غو ببساطة ما هو `Shape` بالتصريح عن واجهة

```go
type Shape interface {
	Area() float64
}
```

ننشئ نوعاً جديداً بالكلمة `type` تماماً كما فعلنا مع `Rectangle` و`Circle`، لكنه هذه المرة `interface` لا `struct`.

بمجرد أن تضيف هذا إلى الشيفرة، ستنجح الاختبارات.

### مهلاً، ماذا؟

هذا مختلف تماماً عن الواجهات في معظم لغات البرمجة الأخرى. فعادةً عليك أن تكتب شيفرة تقول `My type Foo implements interface Bar`.

لكن في حالتنا

* للنوع `Rectangle` طريقة اسمها `Area` تعيد `float64`، لذا فهو يحقق الواجهة `Shape`
* للنوع `Circle` طريقة اسمها `Area` تعيد `float64`، لذا فهو يحقق الواجهة `Shape`
* ليس للنوع `string` طريقة كهذه، لذا فهو لا يحقق الواجهة
* وهكذا.

في غو **تحقيق الواجهات ضمني**. فإن طابق النوع الذي تمرره ما تطلبه الواجهة، فسيتم التصريف.

### فك الاقتران

لاحظ أن دالتنا المساعدة لا تحتاج إلى أن تشغل نفسها بما إذا كان الشكل `Rectangle` أو `Circle` أو `Triangle`. فبالتصريح عن واجهة، تصبح الدالة المساعدة _غير مقترنة_ بالأنواع الملموسة، ولا يكون لديها إلا الطريقة التي تحتاج إليها لأداء عملها.

وهذا الأسلوب في استعمال الواجهات للتصريح عن **ما تحتاج إليه فقط** مهم جداً في تصميم البرمجيات، وسنتناوله بتفصيل أكبر في أقسام لاحقة.

## مزيد من إعادة الهيكلة

والآن بعد أن صار لديك بعض الفهم للبنى، يمكننا تقديم "الاختبارات الجدولية".

[الاختبارات الجدولية (table driven tests)](https://go.dev/wiki/TableDrivenTests) مفيدة حين تريد بناء قائمة من حالات الاختبار يمكن اختبارها بالطريقة نفسها.

```go
func TestArea(t *testing.T) {

	areaTests := []struct {
		shape Shape
		want  float64
	}{
		{Rectangle{12, 6}, 72.0},
		{Circle{10}, 314.1592653589793},
	}

	for _, tt := range areaTests {
		got := tt.shape.Area()
		if got != tt.want {
			t.Errorf("got %g want %g", got, tt.want)
		}
	}

}
```

الصياغة الجديدة الوحيدة هنا هي إنشاء "بنية مجهولة" هي `areaTests`. فنحن نصرّح عن شريحة (slice) من البنى باستعمال `[]struct` بحقلين هما `shape` و`want`، ثم نملأ الشريحة بالحالات.

ثم نمر عليها كما نفعل مع أي شريحة أخرى، مستعملين حقول البنية لتشغيل اختباراتنا.

يمكنك أن ترى كم سيكون سهلاً على المطور أن يضيف شكلاً جديداً، وينفّذ `Area`، ثم يضيفه إلى حالات الاختبار. إضافة إلى ذلك، إن اكتُشف خطأ برمجي في `Area` فمن السهل جداً إضافة حالة اختبار جديدة تختبره قبل إصلاحه.

يمكن أن تكون الاختبارات الجدولية أداة رائعة في صندوق أدواتك، لكن تأكد من أنك تحتاج فعلاً إلى الضجيج الإضافي الذي تضيفه إلى الاختبارات.
فهي مناسبة جداً حين تريد اختبار تنفيذات مختلفة لواجهة، أو حين تكون للبيانات الممررة إلى دالة متطلبات كثيرة مختلفة تحتاج إلى اختبار.

لنوضح كل هذا بإضافة شكل آخر واختباره: المثلث.

## اكتب الاختبار أولاً

إضافة اختبار جديد لشكلنا الجديد سهلة جداً. أضف فقط `{Triangle{12, 6}, 36.0},` إلى قائمتنا.

```go
func TestArea(t *testing.T) {

	areaTests := []struct {
		shape Shape
		want  float64
	}{
		{Rectangle{12, 6}, 72.0},
		{Circle{10}, 314.1592653589793},
		{Triangle{12, 6}, 36.0},
	}

	for _, tt := range areaTests {
		got := tt.shape.Area()
		if got != tt.want {
			t.Errorf("got %g want %g", got, tt.want)
		}
	}

}
```

## حاول تشغيل الاختبار

تذكّر أن تواصل محاولة تشغيل الاختبار، وأن تدع المصرِّف يرشدك نحو الحل.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

`./shapes_test.go:25:4: undefined: Triangle`

لم نعرّف `Triangle` بعد

```go
type Triangle struct {
	Base   float64
	Height float64
}
```

حاول مجدداً

```text
./shapes_test.go:25:8: cannot use Triangle literal (type Triangle) as type Shape in field value:
    Triangle does not implement Shape (missing Area method)
```

يخبرنا أننا لا نستطيع استعمال `Triangle` كشكل لأنه لا يملك الطريقة `Area()`، لذا أضف تنفيذاً فارغاً لتشغيل الاختبار

```go
func (t Triangle) Area() float64 {
	return 0
}
```

أخيراً تُصرَّف الشيفرة ونحصل على الخطأ

`shapes_test.go:31: got 0.00 want 36.00`

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (t Triangle) Area() float64 {
	return (t.Base * t.Height) * 0.5
}
```

وتنجح اختباراتنا!

## أعد الهيكلة

مرة أخرى، التنفيذ جيد، لكن اختباراتنا تحتاج إلى بعض التحسين.

حين تلقي نظرة سريعة على هذا

```
{Rectangle{12, 6}, 72.0},
{Circle{10}, 314.1592653589793},
{Triangle{12, 6}, 36.0},
```

لا يتضح على الفور ما تمثله كل هذه الأعداد، وينبغي أن تسعى إلى أن تكون اختباراتك سهلة الفهم.

لم تَرَ حتى الآن إلا صياغة إنشاء نسخ من البنى `MyStruct{val1, val2}`، لكن يمكنك اختيارياً تسمية الحقول.

لنرَ كيف يبدو ذلك

```
        {shape: Rectangle{Width: 12, Height: 6}, want: 72.0},
        {shape: Circle{Radius: 10}, want: 314.1592653589793},
        {shape: Triangle{Base: 12, Height: 6}, want: 36.0},
```

في كتاب [Test-Driven Development by Example](https://g.co/kgs/yCzDLF) يعيد كينت بيك هيكلة بعض الاختبارات إلى حد معيّن ثم يقرر:

> يخاطبنا الاختبار بوضوح أكبر، كأنه توكيد لحقيقة، **لا سلسلة من العمليات**

(التشديد في الاقتباس من عندي)

والآن تقدّم اختباراتنا، أو بالأحرى قائمة حالات الاختبار، توكيدات (assertions) لحقائق عن الأشكال ومساحاتها.

## تأكد من أن مخرجات اختبارك مفيدة

هل تذكر حين كنا ننفّذ `Triangle` سابقاً وكان لدينا الاختبار الفاشل؟ لقد طبع `shapes_test.go:31: got 0.00 want 36.00`.

عرفنا أن هذا يتعلق بـ`Triangle` لأننا كنا نعمل عليه للتو.
لكن ماذا لو تسلل خطأ برمجي إلى النظام في إحدى 20 حالة في الجدول؟
كيف سيعرف المطور أي حالة فشلت؟
هذه ليست تجربة جيدة للمطور، إذ سيضطر إلى المرور على الحالات يدوياً ليعرف أيها فشلت فعلاً.

يمكننا تغيير رسالة الخطأ إلى `%#v got %g want %g`. فسلسلة التنسيق `%#v` ستطبع البنية مع قيم حقولها، فيرى المطور بلمحة الخصائص التي تُختبر.

ولزيادة قابلية قراءة حالات الاختبار أكثر، يمكننا تغيير اسم الحقل `want` إلى اسم أكثر وصفاً مثل `hasArea`.

ونصيحة أخيرة مع الاختبارات الجدولية هي استعمال `t.Run` وتسمية حالات الاختبار.

فبتغليف كل حالة في `t.Run` ستحصل على مخرجات اختبار أوضح عند الفشل، لأنها ستطبع اسم الحالة

```text
--- FAIL: TestArea (0.00s)
    --- FAIL: TestArea/Rectangle (0.00s)
        shapes_test.go:33: main.Rectangle{Width:12, Height:6} got 72.00 want 72.10
```

ويمكنك تشغيل اختبارات محددة داخل جدولك بالأمر `go test -run TestArea/Rectangle`.

إليك شيفرة اختبارنا النهائية التي تجسّد هذا

```go
func TestArea(t *testing.T) {

	areaTests := []struct {
		name    string
		shape   Shape
		hasArea float64
	}{
		{name: "Rectangle", shape: Rectangle{Width: 12, Height: 6}, hasArea: 72.0},
		{name: "Circle", shape: Circle{Radius: 10}, hasArea: 314.1592653589793},
		{name: "Triangle", shape: Triangle{Base: 12, Height: 6}, hasArea: 36.0},
	}

	for _, tt := range areaTests {
		// using tt.name from the case to use it as the `t.Run` test name
		t.Run(tt.name, func(t *testing.T) {
			got := tt.shape.Area()
			if got != tt.hasArea {
				t.Errorf("%#v got %g want %g", tt.shape, got, tt.hasArea)
			}
		})

	}

}
```

## الخلاصة

كان هذا مزيداً من التمرّن على `TDD`، بالتكرار على حلولنا لمشكلات رياضية بسيطة، وتعلّم ميزات جديدة في اللغة تدفعنا إليها اختباراتنا.

* التصريح عن البنى لإنشاء أنواع بيانات خاصة بك، مما يتيح لك جمع البيانات المترابطة معاً ويجعل قصد شيفرتك أوضح
* التصريح عن الواجهات كي تستطيع تعريف دوال يمكن استعمالها مع أنواع مختلفة ([تعدد الأشكال المعامَلي](https://en.wikipedia.org/wiki/Parametric_polymorphism))
* إضافة الطرق كي تستطيع إضافة وظائف إلى أنواع بياناتك، وكي تستطيع تحقيق الواجهات
* الاختبارات الجدولية لجعل توكيداتك أوضح ومجموعات اختباراتك أسهل في التوسيع والصيانة

كان هذا فصلاً مهماً لأننا بدأنا الآن بتعريف أنواعنا الخاصة. ففي اللغات ثابتة الأنواع مثل غو، القدرة على تصميم أنواعك الخاصة ضرورية لبناء برمجيات سهلة الفهم والتركيب والاختبار.

الواجهات أداة رائعة لإخفاء التعقيد عن الأجزاء الأخرى من النظام. ففي حالتنا، لم تكن _شيفرة_ دالتنا المساعدة في الاختبار تحتاج إلى معرفة الشكل الدقيق الذي تتحقق منه، بل كيف "تسأل" عن مساحته فقط.

وكلما ازددت ألفة بغو، ستبدأ برؤية القوة الحقيقية للواجهات وللمكتبة القياسية. وستتعرّف على واجهات معرّفة في المكتبة القياسية تُستعمل _في كل مكان_، وبتحقيقها في أنواعك الخاصة يمكنك بسرعة كبيرة إعادة استعمال كثير من الوظائف الرائعة.
