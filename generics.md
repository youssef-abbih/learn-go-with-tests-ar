# الأنواع العامة

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/generics)**

سيقدّم لك هذا الفصل مدخلاً إلى الأنواع العامة (generics)، ويبدد تحفظات قد تكون لديك تجاهها، ويعطيك فكرة عن كيفية تبسيط بعض شيفرتك (code) في المستقبل. وبعد قراءته ستعرف كيف تكتب:

- دالة (function) تأخذ وسطاء (arguments) عامة
- هيكل بيانات عاماً


## دوالنا المساعدة الخاصة للاختبار (`AssertEqual` و`AssertNotEqual`)

لاستكشاف الأنواع العامة سنكتب بعض الدوال المساعدة للاختبار.

### التوكيد على الأعداد الصحيحة

لنبدأ بشيء بسيط ونتقدم خطوة خطوة نحو هدفنا

```go
import "testing"

func TestAssertFunctions(t *testing.T) {
	t.Run("asserting on integers", func(t *testing.T) {
		AssertEqual(t, 1, 1)
		AssertNotEqual(t, 1, 2)
	})
}

func AssertEqual(t *testing.T, got, want int) {
	t.Helper()
	if got != want {
		t.Errorf("got %d, want %d", got, want)
	}
}

func AssertNotEqual(t *testing.T, got, want int) {
	t.Helper()
	if got == want {
		t.Errorf("didn't want %d", got)
	}
}
```


### التوكيد على السلاسل النصية

القدرة على التوكيد (assertion) على تساوي الأعداد الصحيحة رائعة، لكن ماذا لو أردنا التوكيد على `string`؟

```go
t.Run("asserting on strings", func(t *testing.T) {
	AssertEqual(t, "hello", "hello")
	AssertNotEqual(t, "hello", "Grace")
})
```

سيظهر لك خطأ (error)

```
# github.com/quii/learn-go-with-tests/generics [github.com/quii/learn-go-with-tests/generics.test]
./generics_test.go:12:18: cannot use "hello" (untyped string constant) as int value in argument to AssertEqual
./generics_test.go:13:21: cannot use "hello" (untyped string constant) as int value in argument to AssertNotEqual
./generics_test.go:13:30: cannot use "Grace" (untyped string constant) as int value in argument to AssertNotEqual
```

إن أخذت وقتك في قراءة الخطأ، فسترى أن المصرِّف (compiler) يعترض على أننا نحاول تمرير `string` إلى دالة تتوقع `integer`.

#### تذكير بأمان الأنواع

إن كنت قد قرأت الفصول السابقة من هذا الكتاب، أو لديك خبرة في اللغات ثابتة الأنواع، فلا ينبغي أن يفاجئك هذا. فمصرِّف غو (Go) يتوقع منك أن تكتب دوالك وبناك وغيرها بوصف الأنواع التي تريد العمل معها.

لا يمكنك تمرير `string` إلى دالة تتوقع `integer`.

ومع أن هذا قد يبدو مجرد شكليات، فقد يكون مفيداً للغاية. فبوصف هذه القيود، فإنك

- تجعل تنفيذ الدوال أبسط. فبوصفك للمصرِّف الأنواع التي تعمل معها، **تقيّد عدد التنفيذات الصالحة الممكنة**. فلا يمكنك "جمع" `Person` و`BankAccount`، ولا يمكنك تكبير أحرف `integer`. وفي البرمجيات كثيراً ما تكون القيود مفيدة للغاية.
- تُمنع من تمرير بيانات إلى دالة لم تقصدها عن طريق الخطأ.

توفر لك غو طريقة لتكون أكثر تجريداً مع أنواعك عبر [الواجهات](./structs-methods-and-interfaces.md)، كي تستطيع تصميم دوال لا تأخذ أنواعاً ملموسة، بل أنواعاً توفر السلوك الذي تحتاج إليه. وهذا يمنحك بعض المرونة مع الحفاظ على أمان الأنواع.

### دالة تأخذ سلسلة نصية أو عدداً صحيحاً؟ (أو أشياء أخرى في الحقيقة)

ومن الخيارات الأخرى في غو لجعل دوالك أكثر مرونة التصريح عن نوع (type) الوسيط على أنه `interface{}`، وهو ما يعني "أي شيء".

جرّب تغيير التواقيع لتستعمل هذا النوع بدلاً من ذلك.

```go
func AssertEqual(got, want interface{})

func AssertNotEqual(got, want interface{})

```

ينبغي أن تُصرَّف الاختبارات الآن وتنجح. وإن حاولت جعلها تفشل، فسترى أن المخرجات رديئة بعض الشيء، لأننا نستعمل سلسلة تنسيق الأعداد الصحيحة `%d` لطباعة رسائلنا، لذا غيّرها إلى الصيغة العامة `%+v` للحصول على مخرجات أفضل لأي نوع من القيم.

### المشكلة في `interface{}`

دوالنا `AssertX` ساذجة إلى حد ما، لكنها من حيث المفهوم لا تختلف كثيراً عن الطريقة التي [توفر بها مكتبات شائعة أخرى هذه الوظيفة](https://github.com/matryer/is/blob/master/is.go#L150)

```go
func (is *I) Equal(a, b interface{})
```

فما المشكلة إذن؟

باستعمال `interface{}` لا يستطيع المصرِّف مساعدتنا حين نكتب شيفرتنا، لأننا لا نخبره بأي شيء مفيد عن أنواع الأشياء الممررة إلى الدالة. جرّب مقارنة نوعين مختلفين.

```go
AssertEqual(1, "1")
```

في هذه الحالة ننجو بفعلتنا؛ فالاختبار (test) يُصرَّف ويفشل كما نأمل، مع أن رسالة الخطأ `got 1, want 1` غير واضحة؛ لكن هل نريد أن نستطيع مقارنة السلاسل النصية بالأعداد الصحيحة؟ وماذا عن مقارنة `Person` بـ`Airport`؟

كتابة دوال تأخذ `interface{}` قد تكون صعبة للغاية وعرضة للأخطاء البرمجية، لأننا _فقدنا_ قيودنا، ولا نملك في وقت التصريف أي معلومات عن أنواع البيانات التي نتعامل معها.

وهذا يعني أن **المصرِّف لا يستطيع مساعدتنا**، وأننا بدلاً من ذلك أكثر عرضة لـ**أخطاء وقت التشغيل** التي قد تؤثر في مستخدمينا، أو تسبب انقطاعات، أو ما هو أسوأ.

كثيراً ما يضطر المطورون إلى استعمال الانعكاس (reflection) لتنفيذ هذه الدوال "العامة" *إحم*، وقد يصبح ذلك معقداً في القراءة والكتابة، وقد يضر بأداء برنامجك.

## دوالنا المساعدة الخاصة للاختبار باستعمال الأنواع العامة

في الوضع المثالي، لا نريد أن نضطر إلى صنع دوال `AssertX` محددة لكل نوع نتعامل معه. بل نود أن تكون لدينا دالة `AssertEqual` _واحدة_ تعمل مع _أي_ نوع، لكنها لا تسمح لك بمقارنة [التفاح بالبرتقال](https://en.wikipedia.org/wiki/Apples_and_oranges).

توفر لنا الأنواع العامة طريقة لصنع تجريدات (كالواجهات) بأن تتيح لنا **وصف قيودنا**. فهي تتيح لنا كتابة دوال لها مستوى من المرونة يشبه ما يوفره `interface{}`، لكنها تحافظ على أمان الأنواع وتوفر تجربة أفضل للمطورين المستدعين.

```go
func TestAssertFunctions(t *testing.T) {
	t.Run("asserting on integers", func(t *testing.T) {
		AssertEqual(t, 1, 1)
		AssertNotEqual(t, 1, 2)
	})

	t.Run("asserting on strings", func(t *testing.T) {
		AssertEqual(t, "hello", "hello")
		AssertNotEqual(t, "hello", "Grace")
	})

	// AssertEqual(t, 1, "1") // uncomment to see the error
}

func AssertEqual[T comparable](t *testing.T, got, want T) {
	t.Helper()
	if got != want {
		t.Errorf("got %v, want %v", got, want)
	}
}

func AssertNotEqual[T comparable](t *testing.T, got, want T) {
	t.Helper()
	if got == want {
		t.Errorf("didn't want %v", got)
	}
}
```

لكتابة دوال عامة في غو، عليك تقديم "معاملات أنواع"، وهي مجرد طريقة منمقة لقول "صِف نوعك العام وأعطه تسمية".

في حالتنا نوع معامل النوع هو `comparable`، وأعطيناه التسمية `T`. وهذه التسمية تتيح لنا بعد ذلك وصف أنواع وسطاء دالتنا (`got, want T`).

نستعمل `comparable` لأننا نريد أن نصف للمصرِّف أننا نرغب في استعمال العاملين `==` و`!=` على الأشياء من النوع `T` في دالتنا، فنحن نريد المقارنة! وإن حاولت تغيير النوع إلى `any`،

```go
func AssertNotEqual[T any](got, want T)
```

فسيظهر لك الخطأ التالي:

```
prog.go2:15:5: cannot compare got != want (operator != not defined for T)
```

وهذا منطقي جداً، لأنك لا تستطيع استعمال هذين العاملين على كل نوع (أي `any` نوع).

### هل الدالة العامة ذات [`T any`](https://go.googlesource.com/proposal/+/refs/heads/master/design/go2draft-type-parameters.md#the-constraint) هي نفسها `interface{}`؟

لننظر في دالتين

```go
func GenericFoo[T any](x, y T)
```

```go
func InterfaceyFoo(x, y interface{})
```

ما الفائدة من الأنواع العامة هنا؟ ألا يصف `any`... أي شيء؟

من حيث القيود، `any` تعني فعلاً "أي شيء"، وكذلك `interface{}`. بل إن `any` أضيفت في الإصدار 1.18 وهي _مجرد اسم بديل لـ`interface{}`_.

الفرق في النسخة العامة أنك _ما زلت تصف نوعاً محدداً_، وهذا يعني أننا ما زلنا نقيّد هذه الدالة لتعمل مع نوع _واحد_ فقط.

وهذا يعني أنك تستطيع استدعاء `InterfaceyFoo` بأي مزيج من الأنواع (مثل `InterfaceyFoo(apple, orange)`). أما `GenericFoo` فما زالت توفر بعض القيود، لأننا قلنا إنها لا تعمل إلا مع نوع _واحد_ هو `T`.

صالح:

- `GenericFoo(apple1, apple2)`
- `GenericFoo(orange1, orange2)`
- `GenericFoo(1, 2)`
- `GenericFoo("one", "two")`

غير صالح (يفشل في التصريف):

- `GenericFoo(apple1, orange1)`
- `GenericFoo("1", 1)`

وإن كانت دالتك تعيد النوع العام، فيستطيع المستدعي أيضاً استعمال النوع كما هو، بدلاً من الاضطرار إلى إجراء توكيد نوع، لأنه حين تعيد الدالة `interface{}` لا يستطيع المصرِّف تقديم أي ضمانات بشأن النوع.

## التالي: أنواع البيانات العامة

سننشئ نوع بيانات [مكدس](https://en.wikipedia.org/wiki/Stack_(abstract_data_type)). ينبغي أن يكون فهم المكدسات مباشراً إلى حد ما من ناحية المتطلبات. فهي مجموعة من العناصر يمكنك أن تدفع (`Push`) العناصر إلى "قمتها"، ولاسترجاع العناصر تسحبها (`Pop`) من القمة (LIFO: آخر من يدخل أول من يخرج).

اختصاراً، حذفت عملية `TDD` التي أوصلتني إلى الشيفرة التالية لمكدس من قيم `int`، ومكدس من قيم `string`.

```go
type StackOfInts struct {
	values []int
}

func (s *StackOfInts) Push(value int) {
	s.values = append(s.values, value)
}

func (s *StackOfInts) IsEmpty() bool {
	return len(s.values) == 0
}

func (s *StackOfInts) Pop() (int, bool) {
	if s.IsEmpty() {
		return 0, false
	}

	index := len(s.values) - 1
	el := s.values[index]
	s.values = s.values[:index]
	return el, true
}

type StackOfStrings struct {
	values []string
}

func (s *StackOfStrings) Push(value string) {
	s.values = append(s.values, value)
}

func (s *StackOfStrings) IsEmpty() bool {
	return len(s.values) == 0
}

func (s *StackOfStrings) Pop() (string, bool) {
	if s.IsEmpty() {
		return "", false
	}

	index := len(s.values) - 1
	el := s.values[index]
	s.values = s.values[:index]
	return el, true
}
```

أنشأت بعض دوال التوكيد الأخرى للمساعدة

```go
func AssertTrue(t *testing.T, got bool) {
	t.Helper()
	if !got {
		t.Errorf("got %v, want true", got)
	}
}

func AssertFalse(t *testing.T, got bool) {
	t.Helper()
	if got {
		t.Errorf("got %v, want false", got)
	}
}
```

وإليك الاختبارات

```go
func TestStack(t *testing.T) {
	t.Run("integer stack", func(t *testing.T) {
		myStackOfInts := new(StackOfInts)

		// check stack is empty
		AssertTrue(t, myStackOfInts.IsEmpty())

		// add a thing, then check it's not empty
		myStackOfInts.Push(123)
		AssertFalse(t, myStackOfInts.IsEmpty())

		// add another thing, pop it back again
		myStackOfInts.Push(456)
		value, _ := myStackOfInts.Pop()
		AssertEqual(t, value, 456)
		value, _ = myStackOfInts.Pop()
		AssertEqual(t, value, 123)
		AssertTrue(t, myStackOfInts.IsEmpty())
	})

	t.Run("string stack", func(t *testing.T) {
		myStackOfStrings := new(StackOfStrings)

		// check stack is empty
		AssertTrue(t, myStackOfStrings.IsEmpty())

		// add a thing, then check it's not empty
		myStackOfStrings.Push("123")
		AssertFalse(t, myStackOfStrings.IsEmpty())

		// add another thing, pop it back again
		myStackOfStrings.Push("456")
		value, _ := myStackOfStrings.Pop()
		AssertEqual(t, value, "456")
		value, _ = myStackOfStrings.Pop()
		AssertEqual(t, value, "123")
		AssertTrue(t, myStackOfStrings.IsEmpty())
	})
}
```

### المشكلات

- الشيفرة الخاصة بكل من `StackOfStrings` و`StackOfInts` متطابقة تقريباً. ومع أن الازدواجية ليست دائماً نهاية العالم، فهي شيفرة أكثر للقراءة والكتابة والصيانة.
- ولأننا نكرر المنطق في نوعين، فقد اضطررنا إلى تكرار الاختبارات أيضاً.

نريد حقاً أن نجسّد _فكرة_ المكدس في نوع واحد، وأن تكون لنا مجموعة واحدة من الاختبارات له. وينبغي أن نرتدي الآن قبعة إعادة الهيكلة (refactoring)، وهذا يعني ألا نغيّر الاختبارات لأننا نريد الحفاظ على السلوك نفسه.

دون الأنواع العامة، هذا ما _يمكننا_ فعله

```go
type StackOfInts = Stack
type StackOfStrings = Stack

type Stack struct {
	values []interface{}
}

func (s *Stack) Push(value interface{}) {
	s.values = append(s.values, value)
}

func (s *Stack) IsEmpty() bool {
	return len(s.values) == 0
}

func (s *Stack) Pop() (interface{}, bool) {
	if s.IsEmpty() {
		var zero interface{}
		return zero, false
	}

	index := len(s.values) - 1
	el := s.values[index]
	s.values = s.values[:index]
	return el, true
}
```

- نجعل تنفيذينا السابقين `StackOfInts` و`StackOfStrings` اسمين بديلين لنوع جديد موحّد هو `Stack`
- أزلنا أمان الأنواع من `Stack` بجعل `values` [شريحة](https://github.com/quii/learn-go-with-tests/blob/main/arrays-and-slices.md) من `interface{}`

لتجربة هذه الشيفرة، عليك إزالة قيود الأنواع من دوال التوكيد لدينا:

```go
func AssertEqual(t *testing.T, got, want interface{})
```

إن فعلت هذا، فستظل اختباراتنا ناجحة. فمن يحتاج إلى الأنواع العامة؟

### مشكلة التخلي عن أمان الأنواع

المشكلة الأولى هي نفسها التي رأيناها مع `AssertEquals`: لقد فقدنا أمان الأنواع. فيمكنني الآن دفع التفاح بـ`Push` إلى مكدس من البرتقال.

وحتى لو كان لدينا الانضباط الكافي لعدم فعل ذلك، فما زال العمل مع الشيفرة مزعجاً، لأن الطرق (methods) حين **تعيد `interface{}` يكون العمل معها فظيعاً**.

أضف الاختبار التالي،

```go
t.Run("interface stack DX is horrid", func(t *testing.T) {
	myStackOfInts := new(StackOfInts)

	myStackOfInts.Push(1)
	myStackOfInts.Push(2)
	firstNum, _ := myStackOfInts.Pop()
	secondNum, _ := myStackOfInts.Pop()
	AssertEqual(t, firstNum+secondNum, 3)
})
```

ستحصل على خطأ من المصرِّف يبيّن ضعف فقدان أمان الأنواع:

```
invalid operation: operator + not defined on firstNum (variable of type interface{})
```

حين تعيد `Pop` قيمة `interface{}` فهذا يعني أن المصرِّف لا يملك أي معلومات عن ماهية البيانات، ولذلك يقيّد ما يمكننا فعله بشدة. فلا يستطيع أن يعرف أنها ينبغي أن تكون عدداً صحيحاً، لذا لا يسمح لنا باستعمال العامل `+`.

وللالتفاف على ذلك، على المستدعي إجراء [توكيد نوع](https://golang.org/ref/spec#Type_assertions) لكل قيمة.

```go
t.Run("interface stack dx is horrid", func(t *testing.T) {
	myStackOfInts := new(StackOfInts)

	myStackOfInts.Push(1)
	myStackOfInts.Push(2)
	firstNum, _ := myStackOfInts.Pop()
	secondNum, _ := myStackOfInts.Pop()

	// get our ints from out interface{}
	reallyFirstNum, ok := firstNum.(int)
	AssertTrue(t, ok) // need to check we definitely got an int out of the interface{}

	reallySecondNum, ok := secondNum.(int)
	AssertTrue(t, ok) // and again!

	AssertEqual(t, reallyFirstNum+reallySecondNum, 3)
})
```

الإزعاج الذي يشع من هذا الاختبار سيتكرر لدى كل مستخدم محتمل لتنفيذ `Stack` لدينا، يا للقرف.

### هياكل البيانات العامة إلى النجدة

تماماً كما تستطيع تعريف وسطاء عامة للدوال، يمكنك تعريف هياكل بيانات عامة.

إليك تنفيذ `Stack` الجديد، الذي يتضمن نوع بيانات عاماً.

```go
type Stack[T any] struct {
	values []T
}

func (s *Stack[T]) Push(value T) {
	s.values = append(s.values, value)
}

func (s *Stack[T]) IsEmpty() bool {
	return len(s.values) == 0
}

func (s *Stack[T]) Pop() (T, bool) {
	if s.IsEmpty() {
		var zero T
		return zero, false
	}

	index := len(s.values) - 1
	el := s.values[index]
	s.values = s.values[:index]
	return el, true
}
```

وإليك الاختبارات، تبيّن أنها تعمل كما نريد، مع أمان أنواع كامل.

```go
func TestStack(t *testing.T) {
	t.Run("integer stack", func(t *testing.T) {
		myStackOfInts := new(Stack[int])

		// check stack is empty
		AssertTrue(t, myStackOfInts.IsEmpty())

		// add a thing, then check it's not empty
		myStackOfInts.Push(123)
		AssertFalse(t, myStackOfInts.IsEmpty())

		// add another thing, pop it back again
		myStackOfInts.Push(456)
		value, _ := myStackOfInts.Pop()
		AssertEqual(t, value, 456)
		value, _ = myStackOfInts.Pop()
		AssertEqual(t, value, 123)
		AssertTrue(t, myStackOfInts.IsEmpty())

		// can get the numbers we put in as numbers, not untyped interface{}
		myStackOfInts.Push(1)
		myStackOfInts.Push(2)
		firstNum, _ := myStackOfInts.Pop()
		secondNum, _ := myStackOfInts.Pop()
		AssertEqual(t, firstNum+secondNum, 3)
	})
}
```

ستلاحظ أن صياغة تعريف هياكل البيانات العامة متسقة مع تعريف الوسطاء العامة للدوال.

```go
type Stack[T any] struct {
	values []T
}
```

إنها _تقريباً_ مثل السابق، كل ما في الأمر أننا نقول إن **نوع المكدس يقيّد نوع القيم التي يمكنك العمل معها**.

بمجرد أن تنشئ `Stack[Orange]` أو `Stack[Apple]`، فإن الطرق المعرّفة على المكدس لن تسمح لك إلا بتمرير النوع المحدد للمكدس الذي تعمل معه، ولن تعيد إلا ذلك النوع:

```go
func (s *Stack[T]) Pop() (T, bool)
```

يمكنك أن تتخيل أنواع التنفيذ وكأنها تُولَّد لك بطريقة ما، بحسب نوع المكدس الذي تنشئه:

```go
func (s *Stack[Orange]) Pop() (Orange, bool)
```

```go
func (s *Stack[Apple]) Pop() (Apple, bool)
```

والآن بعد أن أجرينا إعادة الهيكلة هذه، يمكننا بأمان حذف اختبار مكدس السلاسل النصية، لأننا لا نحتاج إلى إثبات المنطق نفسه مرة بعد مرة.

لاحظ أننا حتى الآن، في أمثلة استدعاء الدوال العامة، لم نحتج إلى تحديد الأنواع العامة. فمثلاً، لاستدعاء `AssertEqual[T]` لا نحتاج إلى تحديد ما هو النوع `T`، إذ يمكن استنتاجه من الوسطاء. أما في الحالات التي لا يمكن فيها استنتاج الأنواع العامة، فعليك تحديد الأنواع عند استدعاء الدالة. والصياغة هي نفسها كما عند تعريف الدالة، أي أنك تحدد الأنواع داخل أقواس مربعة قبل الوسطاء.

ولمثال ملموس، فكّر في صنع دالة بانية لـ`Stack[T]`.
```go
func NewStack[T any]() *Stack[T] {
	return new(Stack[T])
}
```
ولاستعمال هذه الدالة البانية لإنشاء مكدس من الأعداد الصحيحة ومكدس من السلاسل النصية مثلاً، تستدعيها هكذا:
```go
myStackOfInts := NewStack[int]()
myStackOfStrings := NewStack[string]()
```

إليك تنفيذ `Stack` والاختبارات بعد إضافة الدالة البانية.

```go
type Stack[T any] struct {
	values []T
}

func NewStack[T any]() *Stack[T] {
	return new(Stack[T])
}

func (s *Stack[T]) Push(value T) {
	s.values = append(s.values, value)
}

func (s *Stack[T]) IsEmpty() bool {
	return len(s.values) == 0
}

func (s *Stack[T]) Pop() (T, bool) {
	if s.IsEmpty() {
		var zero T
		return zero, false
	}

	index := len(s.values) - 1
	el := s.values[index]
	s.values = s.values[:index]
	return el, true
}
```

```go
func TestStack(t *testing.T) {
	t.Run("integer stack", func(t *testing.T) {
		myStackOfInts := NewStack[int]()

		// check stack is empty
		AssertTrue(t, myStackOfInts.IsEmpty())

		// add a thing, then check it's not empty
		myStackOfInts.Push(123)
		AssertFalse(t, myStackOfInts.IsEmpty())

		// add another thing, pop it back again
		myStackOfInts.Push(456)
		value, _ := myStackOfInts.Pop()
		AssertEqual(t, value, 456)
		value, _ = myStackOfInts.Pop()
		AssertEqual(t, value, 123)
		AssertTrue(t, myStackOfInts.IsEmpty())

		// can get the numbers we put in as numbers, not untyped interface{}
		myStackOfInts.Push(1)
		myStackOfInts.Push(2)
		firstNum, _ := myStackOfInts.Pop()
		secondNum, _ := myStackOfInts.Pop()
		AssertEqual(t, firstNum+secondNum, 3)
	})
}
```


باستعمال نوع بيانات عام:

- قلّلنا ازدواجية المنطق المهم.
- جعلنا `Pop` تعيد `T`، فإن أنشأنا `Stack[int]` نحصل عملياً على `int` من `Pop`؛ ونستطيع الآن استعمال `+` دون الحاجة إلى ألعاب بهلوانية بتوكيدات الأنواع.
- منعنا سوء الاستعمال في وقت التصريف. فلا يمكنك دفع البرتقال بـ`Push` إلى مكدس تفاح.

## الخلاصة

ينبغي أن يكون هذا الفصل قد أعطاك لمحة عن صياغة الأنواع العامة، وبعض الأفكار عن أسباب فائدتها. فقد كتبنا دوال `Assert` خاصة بنا يمكننا إعادة استعمالها بأمان لتجربة أفكار أخرى حول الأنواع العامة، ونفّذنا هيكل بيانات بسيطاً لتخزين أي نوع من البيانات نريده، بطريقة آمنة الأنواع.

### الأنواع العامة أبسط من استعمال `interface{}` في معظم الحالات

إن كنت قليل الخبرة باللغات ثابتة الأنواع، فقد لا تكون الفائدة من الأنواع العامة واضحة على الفور، لكنني أرجو أن تكون أمثلة هذا الفصل قد بيّنت أين لا تكون لغة غو معبّرة بالقدر الذي نريده. وتحديداً، استعمال `interface{}` يجعل شيفرتك:

- أقل أماناً (خلط التفاح بالبرتقال)، وتتطلب معالجة أكثر للأخطاء
- أقل تعبيراً، فـ`interface{}` لا يخبرك بأي شيء عن البيانات
- أكثر ميلاً إلى الاعتماد على [الانعكاس](https://github.com/quii/learn-go-with-tests/blob/main/reflection.md) وتوكيدات الأنواع وغيرها، مما يجعل العمل مع شيفرتك أصعب وأكثر عرضة للأخطاء، لأنه ينقل الفحوص من وقت التصريف إلى وقت التشغيل

استعمال اللغات ثابتة الأنواع فعلُ وصفٍ للقيود. فإن أحسنت فعله، أنشأت شيفرة ليست آمنة وسهلة الاستعمال فحسب، بل أبسط في الكتابة أيضاً، لأن فضاء الحلول الممكنة أصغر.

تمنحنا الأنواع العامة طريقة جديدة للتعبير عن القيود في شيفرتنا، وكما رأينا، ستتيح لنا دمج شيفرة وتبسيطها بطريقة لم تكن ممكنة قبل غو 1.18.

### هل ستحوّل الأنواع العامة غو إلى Java؟

- لا.

هناك كثير من [الخوف وعدم اليقين والشك (FUD)](https://en.wikipedia.org/wiki/Fear,_uncertainty,_and_doubt) في مجتمع غو بشأن أن الأنواع العامة ستقود إلى تجريدات كابوسية وقواعد شيفرة محيّرة. وعادةً ما يُستدرك ذلك بعبارة "يجب استعمالها بحذر".

ومع أن هذا صحيح، فهو ليس نصيحة مفيدة بشكل خاص، لأنه ينطبق على أي ميزة في أي لغة.

قليلون يشتكون من قدرتنا على تعريف الواجهات، التي هي، كالأنواع العامة، وسيلة لوصف القيود داخل شيفرتنا. فحين تصف واجهة (interface) فإنك تتخذ قراراً تصميمياً _قد يكون سيئاً_، والأنواع العامة ليست فريدة في قدرتها على صنع شيفرة محيّرة ومزعجة الاستعمال.

### أنت تستعمل الأنواع العامة بالفعل

فكّر في أنك إن كنت قد استعملت المصفوفات أو الشرائح أو الخرائط، فقد كنت _بالفعل مستهلكاً لشيفرة عامة_.

```
var myApples []Apple
// You can't do this!
append(myApples, Orange{})
```

### التجريد ليس كلمة بذيئة

من السهل السخرية من [AbstractSingletonProxyFactoryBean](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/aop/framework/AbstractSingletonProxyFactoryBean.html)، لكن لا نتظاهر بأن قاعدة شيفرة خالية تماماً من التجريد ليست سيئة أيضاً. فمهمتك أن _تجمع_ المفاهيم المترابطة حين يكون ذلك مناسباً، كي يكون نظامك أسهل في الفهم والتغيير، بدلاً من أن يكون مجموعة من الدوال والأنواع المتفرقة التي يغيب عنها الوضوح.

### [اجعلها تعمل، اجعلها صحيحة، اجعلها سريعة](https://wiki.c2.com/?MakeItWorkMakeItRightMakeItFast#:~:text=%22Make%20it%20work%2C%20make%20it,to%20DesignForPerformance%20ahead%20of%20time.)

يقع الناس في مشكلات مع الأنواع العامة حين يجرّدون بسرعة كبيرة دون معلومات كافية لاتخاذ قرارات تصميمية جيدة.

دورة `TDD` من الأحمر إلى الأخضر إلى إعادة الهيكلة تعني أن لديك إرشاداً أكبر بشأن الشيفرة التي _تحتاج إليها فعلاً_ لتقديم سلوكك، **بدلاً من تخيّل التجريدات مسبقاً**؛ لكن ما زال عليك الحذر.

لا توجد قواعد صارمة هنا، لكن قاوم جعل الأشياء عامة حتى ترى أن لديك تعميماً مفيداً. فحين أنشأنا تنفيذات `Stack` المختلفة، كان من المهم أننا بدأنا بسلوك _ملموس_ مثل `StackOfStrings` و`StackOfInts` مدعوم بالاختبارات. ومن شيفرتنا _الحقيقية_ استطعنا أن نبدأ برؤية أنماط حقيقية، وبدعم من اختباراتنا استطعنا استكشاف إعادة الهيكلة نحو حل أعم.

كثيراً ما ينصحك الناس بألا تعمّم إلا حين ترى الشيفرة نفسها ثلاث مرات، ويبدو هذا قاعدة بداية جيدة.

ومن المسارات الشائعة التي سلكتها في لغات برمجة أخرى:

- دورة `TDD` واحدة لقيادة سلوك ما
- دورة `TDD` أخرى لاختبار بعض السيناريوهات المترابطة الأخرى

> همم، هذه الأشياء تبدو متشابهة، لكن قليلاً من الازدواجية أفضل من الاقتران بتجريد سيئ

- أنام على الفكرة
- دورة `TDD` أخرى

> حسناً، أود أن أرى إن كنت أستطيع تعميم هذا الشيء. الحمد لله أنني ذكي جداً ووسيم لأنني أستعمل `TDD`، فأستطيع إعادة الهيكلة متى شئت، وقد ساعدتني العملية على فهم السلوك الذي أحتاج إليه فعلاً قبل الإفراط في التصميم.

- هذا التجريد يبدو لطيفاً! والاختبارات ما زالت ناجحة، والشيفرة أبسط
- يمكنني الآن حذف عدد من الاختبارات، فقد جسّدت _جوهر_ السلوك وأزلت التفاصيل غير الضرورية
