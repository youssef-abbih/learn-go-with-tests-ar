# تعلّم غو بالاختبارات: توسيع اختبارات القبول (ومدخل خفيف إلى gRPC)

هذا الفصل متابعة لفصل [مدخل إلى اختبارات القبول](https://quii.gitbook.io/learn-go-with-tests/testing-fundamentals/intro-to-acceptance-tests). ويمكنك إيجاد [الشيفرة النهائية لهذا الفصل على GitHub](https://github.com/quii/go-specs-greet).

اختبارات القبول (acceptance tests) أساسية، وتؤثر مباشرة في قدرتك على تطوير نظامك بثقة مع مرور الوقت، بتكلفة تغيير معقولة.

وهي أيضاً أداة رائعة تساعدك على العمل مع الشيفرة الموروثة. فحين تواجه قاعدة شيفرة رديئة بلا أي اختبارات، أرجوك قاوم إغراء البدء بإعادة الهيكلة. بل اكتب بعض اختبارات القبول لتمنحك شبكة أمان تغيّر بها دواخل النظام بحرية دون التأثير في سلوكه الخارجي الوظيفي. فاختبارات القبول لا يلزمها الاهتمام بالجودة الداخلية، لذا فهي مناسبة جداً لهذه المواقف.

وبعد قراءة هذا الفصل، ستدرك أن اختبارات القبول مفيدة للتحقق، ويمكن استعمالها أيضاً في عملية التطوير بمساعدتنا على تغيير نظامنا بقصد ومنهجية أكبر، مما يقلل الجهد المهدر.

## مواد تمهيدية

الإلهام لهذا الفصل وليد سنوات طويلة من الإحباط مع اختبارات القبول. وهناك فيديوهان أنصحك بمشاهدتهما:

- ديف فارلي: [كيف تكتب اختبارات القبول](https://www.youtube.com/watch?v=JDD5EEJgpHU)
- نات برايس: [اختبارات وظيفية من البداية إلى النهاية يمكن أن تعمل في أجزاء من الثانية](https://www.youtube.com/watch?v=Fk4rCn4YLLU)

كتاب "Growing Object Oriented Software" (GOOS) كتاب بالغ الأهمية لكثير من مهندسي البرمجيات، وأنا منهم. والأسلوب الذي يصفه هو الأسلوب الذي أدرّب المهندسين الذين أعمل معهم على اتباعه.

- كتاب [GOOS](http://www.growing-object-oriented-software.com) لنات برايس وستيف فريمان

وأخيراً، تحدثت أنا و[ريا داتاني](https://twitter.com/dattaniriya) عن هذا الموضوع في سياق BDD في محاضرتنا [اختبارات القبول وBDD وغو](https://www.youtube.com/watch?v=ZMWJCk_0WrY).

## تذكير

نتحدث عن اختبارات "الصندوق الأسود" التي تتحقق من أن نظامك يتصرف كما هو متوقع من الخارج، من "**منظور الأعمال**". فالاختبارات لا تصل إلى دواخل النظام الذي تختبره، بل لا يهمها إلا **ما** يفعله نظامك لا **كيف**.

## تشريح اختبارات القبول السيئة

عملت على مدى سنوات طويلة في عدة شركات وفرق. وكل منها أدرك الحاجة إلى اختبارات القبول، أي وسيلة لاختبار النظام من وجهة نظر المستخدم والتحقق من أنه يعمل كما هو مقصود، لكن تكلفة هذه الاختبارات أصبحت دون استثناء تقريباً مشكلة حقيقية للفريق.

- بطيئة التشغيل
- قابلة للكسر بسهولة
- متقلبة
- مكلفة الصيانة، وتبدو وكأنها تجعل تغيير البرنامج أصعب مما ينبغي
- لا تعمل إلا في بيئة معيّنة، مما يسبب حلقات تغذية راجعة بطيئة ورديئة

لنقل إنك تنوي كتابة اختبار قبول حول موقع ويب تبنيه. فتقرر استعمال متصفح ويب بلا واجهة (مثل [Selenium](https://www.selenium.dev)) لمحاكاة مستخدم ينقر الأزرار في موقعك، للتحقق من أنه يفعل ما يجب.

ومع الوقت، يتغير ترميز موقعك مع اكتشاف ميزات جديدة، ويتجادل المهندسون في التفاهات حول ما إذا كان شيء ما ينبغي أن يكون `<article>` أو `<section>` للمرة المليار.

ومع أن فريقك لا يجري إلا تغييرات طفيفة على النظام، بالكاد يلاحظها المستخدم الفعلي، تجد نفسك تهدر وقتاً طويلاً في تحديث اختبارات القبول.

### الاقتران الشديد

فكّر فيما يدفع اختبارات القبول إلى التغير:

- تغيّر في السلوك الخارجي. فإن أردت تغيير ما يفعله النظام، فتغيير مجموعة اختبارات القبول يبدو معقولاً، بل مرغوباً.
- تغيّر في تفاصيل التنفيذ أو إعادة هيكلة. ففي الوضع المثالي لا ينبغي أن يدفع هذا إلى أي تغيير، أو إن دفع فإلى تغيير طفيف.

لكن كثيراً جداً ما يكون الأخير هو سبب اضطرار اختبارات القبول إلى التغير. إلى حد أن المهندسين يصبحون مترددين في تغيير نظامهم بسبب الجهد المتصوَّر لتحديث الاختبارات!

![ريا وأنا نتحدث عن فصل الاهتمامات في اختباراتنا](https://i.imgur.com/bbG6z57.png)

تنبع هذه المشكلات من عدم تطبيق عادات هندسية راسخة ومجرَّبة كتب عنها المؤلفون المذكورون أعلاه. **لا يمكنك كتابة اختبارات القبول كما تكتب اختبارات الوحدة**؛ فهي تتطلب تفكيراً أكبر وممارسات مختلفة.

## تشريح اختبارات القبول الجيدة

إن أردنا اختبارات قبول لا تتغير إلا حين نغيّر السلوك لا تفاصيل التنفيذ، فمن المنطقي أن نحتاج إلى فصل هذين الاهتمامين.

### عن أنواع التعقيد

علينا كمهندسي برمجيات أن نتعامل مع نوعين من التعقيد.

- **التعقيد العَرَضي** هو التعقيد الذي علينا التعامل معه لأننا نعمل مع الحواسيب، أي أشياء مثل الشبكات والأقراص والواجهات البرمجية وغيرها.

- **التعقيد الجوهري** يسمى أحياناً "منطق المجال". وهو القواعد والحقائق الخاصة بمجالك.
  - على سبيل المثال: "إن سحب صاحب الحساب مالاً أكثر من المتاح، فإن حسابه يصبح مكشوفاً". هذه العبارة لا تقول شيئاً عن الحواسيب؛ فقد كانت صحيحة قبل أن تُستعمل الحواسيب في المصارف أصلاً!

ينبغي أن يكون التعبير عن التعقيد الجوهري ممكناً لشخص غير تقني، ومن القيّم أن نكون قد نمذجناه في شيفرة "المجال" لدينا، وفي اختبارات القبول.

### فصل الاهتمامات

ما اقترحه ديف فارلي في الفيديو السابق، وما ناقشناه أنا وريا أيضاً، هو أن تكون لدينا فكرة **المواصفات**. فالمواصفات تصف سلوك النظام الذي نريده دون أن تقترن بالتعقيد العَرَضي أو تفاصيل التنفيذ.

ينبغي أن تبدو لك هذه الفكرة معقولة. ففي شيفرة الإنتاج نسعى كثيراً إلى فصل الاهتمامات وفك الاقتران بين وحدات العمل. ألن تتردد في تقديم `interface` لتتيح لمعالج `HTTP` أن ينفصل عن الاهتمامات غير المتعلقة بـHTTP؟ لنأخذ طريقة التفكير نفسها في اختبارات القبول.

يصف ديف فارلي بنية محددة.

![ديف فارلي عن اختبارات القبول](https://i.imgur.com/nPwpihG.png)

وفي مؤتمر GopherconUK، صغت أنا وريا هذا بمصطلحات غو (Go).

![فصل الاهتمامات](https://i.imgur.com/qdY4RJe.png)

### اختبار بقوة مضاعفة

فصل طريقة تنفيذ المواصفة يتيح لنا إعادة استعمالها في سيناريوهات مختلفة. فيمكننا:

#### جعل مشغّلاتنا قابلة للضبط

وهذا يعني أنك تستطيع تشغيل اختبارات القبول محلياً، وفي بيئة التجهيز، و(في الوضع المثالي) في بيئة الإنتاج.
- كثير جداً من الفرق تبني أنظمتها بحيث يستحيل تشغيل اختبارات القبول محلياً. وهذا يُدخل حلقة تغذية راجعة بطيئة إلى حد لا يُحتمل. ألا تفضّل أن تكون واثقاً من أن اختبارات القبول ستنجح _قبل_ دمج شيفرتك؟ وإن بدأت الاختبارات بالفشل، هل من المقبول ألا تستطيع إعادة إنتاج الفشل محلياً، وأن تضطر بدلاً من ذلك إلى إيداع التغييرات وانتظار نجاحها بعد 20 دقيقة في بيئة مختلفة وأنت تدعو الله؟
- تذكّر أن نجاح اختباراتك في بيئة التجهيز لا يعني أن نظامك سيعمل. فالتطابق بين بيئتي التطوير والإنتاج كذبة بيضاء في أحسن الأحوال. [أنا أختبر في الإنتاج](https://increment.com/testing/i-test-in-production/).
- هناك دائماً فروق بين البيئات قد تؤثر في *سلوك* نظامك. فقد تكون ترويسات التخزين المؤقت في شبكة توزيع المحتوى (CDN) مضبوطة بشكل خاطئ، وقد تتصرف خدمة تعتمد عليها في المراحل التالية بشكل مختلف، وقد تكون قيمة إعداد ما غير صحيحة. لكن ألن يكون جميلاً لو استطعت تشغيل مواصفاتك في بيئة الإنتاج لاكتشاف هذه المشكلات بسرعة؟

#### توصيل مشغّلات _مختلفة_ لاختبار أجزاء أخرى من نظامك

هذه المرونة تتيح لنا اختبار السلوك على مستويات مختلفة من التجريد والطبقات المعمارية، مما يتيح لنا اختبارات أكثر تركيزاً تتجاوز اختبارات الصندوق الأسود.
- فمثلاً، قد تكون لديك صفحة ويب خلفها واجهة برمجية. فلماذا لا تستعمل المواصفة نفسها لاختبار كليهما؟ يمكنك استعمال متصفح ويب بلا واجهة لصفحة الويب، واستدعاءات HTTP للواجهة البرمجية.
- وبأخذ هذه الفكرة أبعد، نريد في الوضع المثالي أن **تنمذج الشيفرة التعقيد الجوهري** (كشيفرة "مجال")، لذا ينبغي أن نستطيع أيضاً استعمال مواصفاتنا في اختبارات الوحدة. وهذا سيعطينا تغذية راجعة سريعة بأن التعقيد الجوهري في نظامنا منمذج ويتصرف بشكل صحيح.


### اختبارات قبول تتغير للأسباب الصحيحة

بهذا الأسلوب، يكون السبب الوحيد لتغير مواصفاتك هو تغير سلوك النظام، وهذا معقول.

- إن اضطرت واجهتك البرمجية عبر HTTP إلى التغير، فلديك مكان واحد واضح لتحديثه، وهو المشغّل.
- وإن تغير ترميزك، فحدّث مرة أخرى المشغّل المعني.

ومع نمو نظامك، ستجد نفسك تعيد استعمال المشغّلات في عدة اختبارات، مما يعني مرة أخرى أنه إن تغيرت تفاصيل التنفيذ فلا يلزمك إلا تحديث مكان واحد واضح عادةً.

حين يُطبق هذا الأسلوب كما ينبغي، يمنحنا مرونة في تفاصيل التنفيذ واستقراراً في المواصفات. والأهم أنه يوفر بنية بسيطة وواضحة لإدارة التغيير، وهذا يصبح ضرورياً مع نمو النظام وفريقه.

### اختبارات القبول كأسلوب لتطوير البرمجيات

ناقشنا أنا وريا في محاضرتنا اختبارات القبول وعلاقتها بـBDD. وتحدثنا عن أن بدء عملك بمحاولة _فهم المشكلة التي تحاول حلها_ والتعبير عنها كمواصفة يساعد على تركيز قصدك، وهو طريقة رائعة لبدء العمل.

تعرّفت على طريقة العمل هذه أول مرة في كتاب GOOS. ولخّصت الأفكار قبل فترة في مدونتي. إليك مقتطفاً من تدوينتي [لماذا TDD](https://quii.dev/The_Why_of_TDD)

---

يركز `TDD` على أن يتيح لك التصميم للسلوك الذي تحتاج إليه بالضبط، بشكل تكراري. فحين تبدأ في منطقة جديدة، عليك تحديد سلوك أساسي ضروري وتقليص النطاق بحزم.

اتبع أسلوباً "من الأعلى إلى الأسفل"، مبتدئاً باختبار قبول (AT) يختبر السلوك من الخارج. وسيعمل هذا كنجم شمال لجهودك. وكل ما ينبغي أن تركز عليه هو جعل ذلك الاختبار ينجح. والأرجح أن يظل هذا الاختبار فاشلاً لبعض الوقت ريثما تطوّر ما يكفي من الشيفرة لجعله ينجح.

![](https://i.imgur.com/pxTaYu4.png)

بمجرد إعداد اختبار القبول، يمكنك الانتقال إلى عملية `TDD` لاستخلاص ما يكفي من الوحدات لجعل اختبار القبول ينجح. والحيلة ألا تقلق كثيراً بشأن التصميم في هذه المرحلة؛ بل اكتب ما يكفي من الشيفرة لجعل اختبار القبول ينجح، لأنك ما زلت تتعلم المشكلة وتستكشفها.

اتخاذ هذه الخطوة الأولى كثيراً ما يكون أوسع مما تظن، من إعداد خوادم الويب والتوجيه والإعدادات وغير ذلك، ولهذا فإن إبقاء نطاق العمل صغيراً أمر ضروري. نريد أن نخطو تلك الخطوة الإيجابية الأولى على لوحتنا البيضاء، وأن تكون مدعومة باختبار قبول ناجح، كي نواصل التقدم بسرعة وأمان.

![](https://i.imgur.com/t5y5opw.png)

وأثناء التطوير، أصغِ إلى اختباراتك، فينبغي أن تعطيك إشارات تساعدك على دفع تصميمك في اتجاه أفضل، لكن مرة أخرى مع الارتكاز على السلوك لا على خيالنا.

وعادةً، ستكبر "وحدتك" الأولى التي تقوم بالعمل الشاق لجعل اختبار القبول ينجح أكثر مما هو مريح، حتى لهذا القدر الصغير من السلوك. وهنا يمكنك أن تبدأ بالتفكير في كيفية تقسيم المشكلة وتقديم متعاونين جدد.

![](https://i.imgur.com/UYqd7Cq.png)

وهنا تكون بدائل الاختبار (test doubles)، مثل البدائل المزيفة والبدائل الوهمية، مفيدة، لأن معظم التعقيد الذي يعيش داخل البرمجيات لا يكمن عادةً في تفاصيل التنفيذ، بل "بين" الوحدات وفي طريقة تفاعلها.

#### مخاطر الأسلوب من الأسفل إلى الأعلى

هذا أسلوب "من الأعلى إلى الأسفل" لا "من الأسفل إلى الأعلى". وللأسلوب من الأسفل إلى الأعلى استعمالاته، لكنه يحمل عنصراً من المخاطرة. فببناء "خدمات" وشيفرة دون دمجها في تطبيقك بسرعة ودون التحقق منها باختبار عالي المستوى، **فإنك تخاطر بهدر جهد كبير على أفكار غير متحقق منها**.

وهذه خاصية حاسمة في الأسلوب المقاد باختبارات القبول، إذ نستعمل الاختبارات للحصول على تحقق حقيقي من شيفرتنا.

مرات كثيرة جداً صادفت مهندسين صنعوا جزءاً من الشيفرة، بمعزل عن غيره ومن الأسفل إلى الأعلى، يظنون أنه سيؤدي مهمة ما، لكنه:

- لا يعمل كما نريد
- يفعل أشياء لا نحتاج إليها
- لا يندمج بسهولة
- يتطلب على أي حال قدراً هائلاً من إعادة الكتابة

وهذا هدر.

## كفى كلاماً، حان وقت الشيفرة

على خلاف الفصول الأخرى، ستحتاج إلى تثبيت [Docker](https://www.docker.com) لأننا سنشغّل تطبيقاتنا في حاويات. ونفترض في هذه المرحلة من الكتاب أنك مرتاح لكتابة شيفرة غو، والاستيراد من حزم مختلفة، وما إلى ذلك.

أنشئ مشروعاً جديداً بالأمر `go mod init github.com/quii/go-specs-greet` (يمكنك وضع ما تشاء هنا، لكن إن غيّرت المسار فعليك تغيير كل الاستيرادات الداخلية لتطابقه)

أنشئ مجلداً باسم `specifications` لاحتواء مواصفاتنا، وأضف ملفاً باسم `greet.go`

```go
package specifications

import (
	"testing"

	"github.com/alecthomas/assert/v2"
)

type Greeter interface {
	Greet() (string, error)
}

func GreetSpecification(t testing.TB, greeter Greeter) {
	got, err := greeter.Greet()
	assert.NoError(t, err)
	assert.Equal(t, got, "Hello, world")
}
```

تتولى بيئة التطوير المتكاملة لدي (Goland) عناء إضافة التبعيات، لكن إن احتجت إلى فعل ذلك يدوياً، فستكتب

`go get github.com/alecthomas/assert/v2`

بالنظر إلى تصميم فارلي لاختبارات القبول (المواصفة ثم اللغة الخاصة بالمجال ثم المشغّل ثم النظام)، صارت لدينا الآن مواصفة منفصلة عن التنفيذ. فهي لا تعرف _كيف_ نحيّي بـ`Greet` ولا تهتم بذلك؛ بل لا يهمها إلا التعقيد الجوهري لمجالنا. صحيح أن هذا التعقيد ليس كبيراً الآن، لكننا سنوسّع المواصفة لإضافة مزيد من الوظائف مع تقدمنا. فمن المهم دائماً أن نبدأ صغاراً!

يمكنك أن تعدّ الواجهة الخطوة الأولى من لغتنا الخاصة بالمجال (DSL)؛ ومع نمو المشروع قد تجد الحاجة إلى تجريد مختلف، لكن هذا جيد في الوقت الحالي.

في هذه المرحلة، قد يدفع هذا القدر من الشكليات لفصل مواصفتنا عن التنفيذ بعض الناس إلى اتهامنا بـ"الإفراط في التجريد". **أعدك بأن اختبارات القبول المقترنة بالتنفيذ أكثر من اللازم تصبح عبئاً حقيقياً على الفرق الهندسية**. وأنا واثق من أن معظم اختبارات القبول الموجودة في العالم مكلفة الصيانة بسبب هذا الاقتران غير المناسب، لا العكس، أي الإفراط في التجريد.

يمكننا استعمال هذه المواصفة للتحقق من أي "نظام" يستطيع التحية بـ`Greet`.

### النظام الأول: واجهة برمجية عبر HTTP

نحتاج إلى تقديم "خدمة تحية" عبر HTTP. لذا علينا أن ننشئ:

1. **مشغّلاً**. في هذه الحالة، يُتعامل مع نظام HTTP باستعمال **عميل HTTP**. وستعرف هذه الشيفرة كيف تعمل مع واجهتنا البرمجية. فالمشغّلات تترجم اللغات الخاصة بالمجال إلى استدعاءات خاصة بالنظام؛ وفي حالتنا سيحقق المشغّل الواجهة التي تعرّفها المواصفات.
2. **خادم HTTP** بواجهة برمجية للتحية
3. **اختباراً**، مسؤولاً عن إدارة دورة حياة تشغيل الخادم، ثم توصيل المشغّل بالمواصفة لتشغيلها كاختبار

## اكتب الاختبار أولاً

قد تكون العملية الأولية لإنشاء اختبار صندوق أسود يصرّف برنامجك ويشغّله، وينفّذ الاختبار، ثم ينظف كل شيء، مجهدة إلى حد كبير. ولهذا يُفضَّل فعلها في بداية مشروعك بأقل قدر من الوظائف. وعادةً أبدأ كل مشاريعي بتنفيذ خادم "hello world"، مع إعداد كل اختباراتي وجاهزيتها لأبني الوظائف الفعلية بسرعة.

قد يستغرق الاعتياد على النموذج الذهني لـ"المواصفات" و"المشغّلات" و"اختبارات القبول" بعض الوقت، فتابع بعناية. وقد يكون من المفيد "العمل بالعكس" بمحاولة استدعاء المواصفة أولاً.

أنشئ بنية تضم البرنامج الذي ننوي إطلاقه.

`mkdir -p cmd/httpserver`

داخل المجلد الجديد، أنشئ ملفاً جديداً باسم `greeter_server_test.go`، وأضف ما يلي.

```go
package main_test

import (
	"testing"

	"github.com/quii/go-specs-greet/specifications"
)

func TestGreeterServer(t *testing.T) {
	specifications.GreetSpecification(t, nil)
}
```

نريد تشغيل مواصفتنا في اختبار غو. ولدينا بالفعل الوصول إلى `*testing.T`، فهذا هو الوسيط (argument) الأول، لكن ماذا عن الثاني؟

النوع `specifications.Greeter` واجهة (interface)، وسنحققها بـ`Driver` بتغيير شيفرة `TestGreeterServer` الجديدة إلى ما يلي:

```go
import (
	go_specs_greet "github.com/quii/go-specs-greet"
)

func TestGreeterServer(t *testing.T) {
	driver := go_specs_greet.Driver{BaseURL: "http://localhost:8080"}
	specifications.GreetSpecification(t, driver)
}
```

سيكون من المستحسن أن يكون `Driver` قابلاً للضبط لتشغيله على بيئات مختلفة، بما فيها البيئة المحلية، لذا أضفنا الحقل `BaseURL`.

## حاول تشغيل الاختبار

```
./greeter_server_test.go:46:12: undefined: go_specs_greet.Driver
```

ما زلنا نمارس `TDD` هنا! إنها خطوة أولى كبيرة علينا اتخاذها؛ فعلينا إنشاء بعض الملفات وكتابة شيفرة ربما أكثر مما اعتدنا عادةً، لكن هذا كثيراً ما يكون الحال حين تبدأ. ومن المهم جداً أن نحاول تذكّر قواعد خطوة الأحمر.

> ارتكب من الخطايا ما يلزم لجعل الاختبار ينجح

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

أمسك أنفك، وتذكّر أننا نستطيع إعادة الهيكلة حين ينجح الاختبار. إليك شيفرة المشغّل في `driver.go`، التي سنضعها في جذر المشروع:

```go
package go_specs_greet

import (
	"io"
	"net/http"
)

type Driver struct {
	BaseURL string
}

func (d Driver) Greet() (string, error) {
	res, err := http.Get(d.BaseURL + "/greet")
	if err != nil {
		return "", err
	}
	defer res.Body.Close()
	greeting, err := io.ReadAll(res.Body)
	if err != nil {
		return "", err
	}
	return string(greeting), nil
}
```


ملاحظات:

- قد تقول إن عليّ كتابة اختبارات لاستخلاص الحالات المختلفة لـ`if err != nil`، لكن بحسب خبرتي، ما دمت لا تفعل أي شيء بـ`err`، فإن الاختبارات التي تقول "أنت تعيد الخطأ الذي تحصل عليه" قليلة القيمة نسبياً.
- **لا ينبغي أن تستعمل عميل HTTP الافتراضي**. لاحقاً سنمرر عميل HTTP لضبطه بمهل زمنية وغيرها، لكننا الآن نحاول فقط الوصول إلى اختبار ناجح.
-  في `greeter_server_test.go` استدعينا الدالة `Driver` من الحزمة `go_specs_greet` التي أنشأناها الآن، فلا تنسَ إضافة `github.com/quii/go-specs-greet` إلى استيراداته.
حاول إعادة تشغيل الاختبارات؛ ينبغي أن تُصرَّف الآن لكنها لا تنجح.

```
Get "http://localhost:8080/greet": dial tcp [::1]:8080: connect: connection refused
```

لدينا `Driver`، لكننا لم نشغّل تطبيقنا بعد، لذا لا يستطيع إجراء طلب HTTP. نحتاج إلى أن ينسّق اختبار القبول بناء نظامنا وتشغيله وأخيراً قتله، كي يعمل الاختبار.

### تشغيل تطبيقنا

من الشائع أن تبني الفرق صور Docker لأنظمتها لنشرها، لذا سنفعل الشيء نفسه في اختبارنا

ولمساعدتنا على استعمال Docker في اختباراتنا، سنستعمل [Testcontainers](https://golang.testcontainers.org). فهي تمنحنا طريقة برمجية لبناء صور Docker وإدارة دورات حياة الحاويات.

`go get github.com/testcontainers/testcontainers-go`

يمكنك الآن تعديل `cmd/httpserver/greeter_server_test.go` ليصبح كما يلي:

```go
package main_test

import (
	"context"
	"testing"

	"github.com/alecthomas/assert/v2"
	go_specs_greet "github.com/quii/go-specs-greet"
	"github.com/quii/go-specs-greet/specifications"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"
)

func TestGreeterServer(t *testing.T) {
	ctx := context.Background()

	req := testcontainers.ContainerRequest{
		FromDockerfile: testcontainers.FromDockerfile{
			Context:    "../../.",
			Dockerfile: "./cmd/httpserver/Dockerfile",
			// set to false if you want less spam, but this is helpful if you're having troubles
			PrintBuildLog: true,
		},
		ExposedPorts: []string{"8080:8080"},
		WaitingFor:   wait.ForHTTP("/").WithPort("8080"),
	}
	container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: req,
		Started:          true,
	})
	assert.NoError(t, err)
	t.Cleanup(func() {
		assert.NoError(t, container.Terminate(ctx))
	})

	driver := go_specs_greet.Driver{BaseURL: "http://localhost:8080"}
	specifications.GreetSpecification(t, driver)
}
```

حاول تشغيل الاختبار.

```
=== RUN   TestGreeterHandler
2022/09/10 18:49:44 Starting container id: 03e8588a1be4 image: docker.io/testcontainers/ryuk:0.3.3
2022/09/10 18:49:45 Waiting for container id 03e8588a1be4 image: docker.io/testcontainers/ryuk:0.3.3
2022/09/10 18:49:45 Container is ready id: 03e8588a1be4 image: docker.io/testcontainers/ryuk:0.3.3
    greeter_server_test.go:32: Did not expect an error but got:
        Error response from daemon: Cannot locate specified Dockerfile: ./cmd/httpserver/Dockerfile: failed to create container
--- FAIL: TestGreeterHandler (0.59s)
```

نحتاج إلى إنشاء `Dockerfile` لبرنامجنا. داخل المجلد `httpserver`، أنشئ `Dockerfile` وأضف ما يلي.

```dockerfile
# Make sure to specify the same Go version as the one in the go.mod file.
# For example, golang:1.22.1-alpine.
FROM golang:1.18-alpine

WORKDIR /app

COPY go.mod ./

RUN go mod download

COPY . .

RUN go build -o svr cmd/httpserver/*.go

EXPOSE 8080
CMD [ "./svr" ]
```

لا تقلق كثيراً بشأن التفاصيل هنا؛ فيمكن تحسينها وتهذيبها، لكنها تكفي لهذا المثال. وميزة أسلوبنا هنا أننا نستطيع لاحقاً تحسين `Dockerfile` ويكون لدينا اختبار يثبت أنه يعمل كما نقصد. وهذه نقطة قوة حقيقية لامتلاك اختبارات الصندوق الأسود!

حاول إعادة تشغيل الاختبار؛ ينبغي أن يعترض على عدم القدرة على بناء الصورة. وهذا طبيعي، لأننا لم نكتب برنامجاً لبنائه بعد!

لكي يُنفَّذ الاختبار بالكامل، سنحتاج إلى إنشاء برنامج يستمع على `8080`، لكن **هذا كل شيء**. التزم بانضباط `TDD`، ولا تكتب شيفرة الإنتاج التي ستجعل الاختبار ينجح حتى نتحقق من أن الاختبار يفشل كما نتوقع.

أنشئ `main.go` داخل المجلد `httpserver` بما يلي

```go
package main

import (
	"log"
	"net/http"
)

func main() {
	handler := http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
	})
	if err := http.ListenAndServe(":8080", handler); err != nil {
		log.Fatal(err)
	}
}
```

حاول تشغيل الاختبار مجدداً، وينبغي أن يفشل بما يلي.

```
    greet.go:16: Expected values to be equal:
        +Hello, World
        \ No newline at end of file
--- FAIL: TestGreeterHandler (2.09s)
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

حدّث المعالج ليتصرف كما تريد مواصفتنا

```go
import (
	"fmt"
	"log"
	"net/http"
)

func main() {
	handler := http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		fmt.Fprint(w, "Hello, world")
	})
	if err := http.ListenAndServe(":8080", handler); err != nil {
		log.Fatal(err)
	}
}
```

## أعد الهيكلة

مع أن هذا ليس إعادة هيكلة من الناحية التقنية، فلا ينبغي أن نعتمد على عميل HTTP الافتراضي، لذا لنغيّر `Driver` بحيث نستطيع تقديم عميل، يعطيه إياه اختبارنا.

```go
import (
	"io"
	"net/http"
)

type Driver struct {
	BaseURL string
	Client  *http.Client
}

func (d Driver) Greet() (string, error) {
	res, err := d.Client.Get(d.BaseURL + "/greet")
	if err != nil {
		return "", err
	}
	defer res.Body.Close()
	greeting, err := io.ReadAll(res.Body)
	if err != nil {
		return "", err
	}
	return string(greeting), nil
}
```

في اختبارنا في `cmd/httpserver/greeter_server_test.go`، حدّث إنشاء المشغّل ليمرر عميلاً.

```go
client := http.Client{
	Timeout: 1 * time.Second,
}

driver := go_specs_greet.Driver{BaseURL: "http://localhost:8080", Client: &client}
specifications.GreetSpecification(t, driver)
```

من الممارسات الجيدة إبقاء `main.go` بأبسط ما يمكن؛ فلا ينبغي أن يهتم إلا بتركيب لبنات البناء التي تصنعها في تطبيق.

أنشئ ملفاً في جذر المشروع باسم `handler.go` وانقل شيفرتنا إليه.

```go
package go_specs_greet

import (
	"fmt"
	"net/http"
)

func Handler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, "Hello, world")
}
```

حدّث `main.go` ليستورد المعالج ويستعمله بدلاً من ذلك.

```go
package main

import (
	"net/http"

	go_specs_greet "github.com/quii/go-specs-greet"
)

func main() {
	handler := http.HandlerFunc(go_specs_greet.Handler)
	http.ListenAndServe(":8080", handler)
}
```

## تأمّل

بدت الخطوة الأولى مجهدة. فقد أنشأنا عدة ملفات `go` لإنشاء معالج HTTP يعيد سلسلة نصية ثابتة واختباره. لكن شكليات "التكرار رقم 0" وإعداده سيخدماننا جيداً في التكرارات التالية.

ينبغي أن يكون تغيير الوظائف بسيطاً ومتحكماً به، بقيادته عبر المواصفة والتعامل مع أي تغييرات تجبرنا عليها. والآن بعد أن صار `DockerFile` و`testcontainers` مُعدَّين لاختبار القبول، لا ينبغي أن نضطر إلى تغيير هذه الملفات ما لم تتغير طريقة بناء تطبيقنا.

سنرى هذا في متطلبنا التالي: تحية شخص معيّن.

## اكتب الاختبار أولاً

عدّل مواصفتنا

```go
package specifications

import (
	"testing"

	"github.com/alecthomas/assert/v2"
)

type Greeter interface {
	Greet(name string) (string, error)
}

func GreetSpecification(t testing.TB, greeter Greeter) {
	got, err := greeter.Greet("Mike")
	assert.NoError(t, err)
	assert.Equal(t, got, "Hello, Mike")
}
```

لكي نستطيع تحية أشخاص محددين، علينا تغيير واجهة نظامنا لتقبل معاملاً (parameter) باسم `name`.

## حاول تشغيل الاختبار

```
./greeter_server_test.go:48:39: cannot use driver (variable of type go_specs_greet.Driver) as type specifications.Greeter in argument to specifications.GreetSpecification:
	go_specs_greet.Driver does not implement specifications.Greeter (wrong type for Greet method)
		have Greet() (string, error)
		want Greet(name string) (string, error)
```

التغيير في المواصفة يعني أن مشغّلنا يحتاج إلى تحديث.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

حدّث المشغّل بحيث يحدد قيمة استعلام `name` في الطلب، ليطلب تحية `name` معيّن.

```go
import "io"

func (d Driver) Greet(name string) (string, error) {
	res, err := d.Client.Get(d.BaseURL + "/greet?name=" + name)
	if err != nil {
		return "", err
	}
	defer res.Body.Close()
	greeting, err := io.ReadAll(res.Body)
	if err != nil {
		return "", err
	}
	return string(greeting), nil
}
```

ينبغي أن يعمل الاختبار الآن، وأن يفشل.

```
    greet.go:16: Expected values to be equal:
        -Hello, world
        \ No newline at end of file
        +Hello, Mike
        \ No newline at end of file
--- FAIL: TestGreeterHandler (1.92s)
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

استخرج `name` من الطلب وألقِ التحية.

```go
import (
	"fmt"
	"net/http"
)

func Handler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello, %s", r.URL.Query().Get("name"))
}
```

ينبغي أن ينجح الاختبار الآن.

## أعد الهيكلة

في فصل [عودة إلى معالجات HTTP](https://github.com/quii/learn-go-with-tests/blob/main/http-handlers-revisited.md) ناقشنا أهمية ألا تكون معالجات HTTP مسؤولة إلا عن اهتمامات HTTP؛ وأن يعيش أي "منطق مجال" خارج المعالج. وهذا يتيح لنا تطوير منطق المجال بمعزل عن HTTP، مما يجعل اختباره وفهمه أبسط.

لنفصل هذه الاهتمامات.

حدّث معالجنا في `./handler.go` كما يلي:

```go
func Handler(w http.ResponseWriter, r *http.Request) {
	name := r.URL.Query().Get("name")
	fmt.Fprint(w, Greet(name))
}
```

أنشئ ملفاً جديداً `./greet.go`:
```go
package go_specs_greet

import "fmt"

func Greet(name string) string {
	return fmt.Sprintf("Hello, %s", name)
}
```

## استطراد قصير إلى نمط التصميم "المحوّل"

والآن بعد أن فصلنا منطق مجالنا في تحية الناس إلى دالة منفصلة، صرنا أحراراً في كتابة اختبارات وحدة لدالة التحية. وهذا بلا شك أبسط بكثير من اختبارها عبر مواصفة تمر بمشغّل يتصل بخادم ويب، للحصول على سلسلة نصية!

ألن يكون جميلاً لو استطعنا إعادة استعمال مواصفتنا هنا أيضاً؟ ففي النهاية، الغاية من المواصفة أنها منفصلة عن تفاصيل التنفيذ. وإن كانت المواصفة تجسّد **التعقيد الجوهري** لدينا، وكانت شيفرة "المجال" يُفترض أن تنمذجه، فينبغي أن نستطيع استعمالهما معاً.

لنجرّب ذلك بإنشاء  `./greet_test.go` كما يلي:

```go
package go_specs_greet_test

import (
	"testing"

	go_specs_greet "github.com/quii/go-specs-greet"
	"github.com/quii/go-specs-greet/specifications"
)

func TestGreet(t *testing.T) {
	specifications.GreetSpecification(t, go_specs_greet.Greet)
}

```

سيكون هذا جميلاً، لكنه لا يعمل

```
./greet_test.go:11:39: cannot use go_specs_greet.Greet (value of type func(name string) string) as type specifications.Greeter in argument to specifications.GreetSpecification:
	func(name string) string does not implement specifications.Greeter (missing Greet method)
```

تريد مواصفتنا شيئاً له طريقة (method) اسمها `Greet()`، لا دالة.

خطأ التصريف محبط؛ فلدينا شيء "نعرف" أنه `Greeter`، لكنه ليس تماماً في **الشكل** الصحيح ليسمح لنا المصرِّف باستعماله. وهذا ما يعالجه نمط **المحوّل**.

> في [هندسة البرمجيات](https://en.wikipedia.org/wiki/Software_engineering)، **نمط المحوّل** [نمط تصميم برمجي](https://en.wikipedia.org/wiki/Software_design_pattern) (يُعرف أيضاً بـ[الغلاف](https://en.wikipedia.org/wiki/Wrapper_function)، وهي تسمية بديلة يشترك فيها مع [نمط المزخرِف](https://en.wikipedia.org/wiki/Decorator_pattern)) يتيح استعمال [واجهة](https://en.wikipedia.org/wiki/Interface_(computer_science)) [صنف](https://en.wikipedia.org/wiki/Class_(computer_science)) موجود كواجهة أخرى.[[1\]](https://en.wikipedia.org/wiki/Adapter_pattern#cite_note-HeadFirst-1) وكثيراً ما يُستعمل لجعل الأصناف الموجودة تعمل مع غيرها دون تعديل [شيفرتها المصدرية](https://en.wikipedia.org/wiki/Source_code).

كثير من الكلمات المنمقة لشيء بسيط نسبياً، وهذا كثيراً ما يكون الحال مع أنماط التصميم، ولهذا يميل الناس إلى التبرم منها. لكن قيمة أنماط التصميم ليست في تنفيذات محددة، بل في كونها لغة لوصف حلول محددة لمشكلات شائعة يواجهها المهندسون. فإن كان لدى فريقك مفردات مشتركة، قلّ الاحتكاك في التواصل.

أضف هذه الشيفرة في `./specifications/adapters.go`

```go
type GreetAdapter func(name string) string

func (g GreetAdapter) Greet(name string) (string, error) {
	return g(name), nil
}
```

يمكننا الآن استعمال المحوّل في اختبارنا لتوصيل الدالة `Greet` بالمواصفة.

```go
package go_specs_greet_test

import (
	"testing"

	gospecsgreet "github.com/quii/go-specs-greet"
	"github.com/quii/go-specs-greet/specifications"
)

func TestGreet(t *testing.T) {
	specifications.GreetSpecification(
		t,
		specifications.GreetAdapter(gospecsgreet.Greet),
	)
}
```

نمط المحوّل مفيد حين يكون لديك نوع يُظهر السلوك الذي تريده واجهة ما، لكنه ليس في الشكل الصحيح.

## تأمّل

بدا تغيير السلوك بسيطاً، أليس كذلك؟ حسناً، ربما كان ذلك ببساطة بسبب طبيعة المشكلة، لكن طريقة العمل هذه تمنحك الانضباط، وطريقة بسيطة قابلة للتكرار لتغيير نظامك من الأعلى إلى الأسفل:

- حلّل مشكلتك وحدد تحسيناً طفيفاً لنظامك يدفعك في الاتجاه الصحيح
- جسّد التعقيد الجوهري الجديد في مواصفة
- اتبع أخطاء التصريف حتى يعمل اختبار القبول
- حدّث تنفيذك ليتصرف النظام وفقاً للمواصفة
- أعد الهيكلة

بعد عناء التكرار الأول، لم نحتج إلى تعديل شيفرة اختبار القبول لأن لدينا فصلاً بين المواصفات والمشغّلات والتنفيذ. وتطلّب تغيير مواصفتنا تحديث المشغّل ثم التنفيذ أخيراً، لكن الشيفرة المتكررة حول _كيفية_ تشغيل النظام كحاوية لم تتأثر.

وحتى مع عبء بناء صورة Docker لتطبيقنا وتشغيل الحاوية، فإن حلقة التغذية الراجعة لاختبار تطبيقنا **كله** متقاربة جداً:

```
quii@Chriss-MacBook-Pro go-specs-greet % go test ./...
ok  	github.com/quii/go-specs-greet	0.181s
ok  	github.com/quii/go-specs-greet/cmd/httpserver	2.221s
?   	github.com/quii/go-specs-greet/specifications	[no test files]
```

تخيّل الآن أن مديرتك التقنية قررت أن gRPC هو _المستقبل_. وهي تريد منك أن تتيح هذه الوظيفة نفسها عبر خادم gRPC مع الحفاظ على خادم HTTP الحالي.

هذا مثال على **التعقيد العَرَضي**. تذكّر أن التعقيد العَرَضي هو التعقيد الذي علينا التعامل معه لأننا نعمل مع الحواسيب، أي أشياء مثل الشبكات والأقراص والواجهات البرمجية وغيرها. **فالتعقيد الجوهري لم يتغير**، لذا لا ينبغي أن نضطر إلى تغيير مواصفاتنا.

كثير من بنى المستودعات وأنماط التصميم تتعامل أساساً مع فصل أنواع التعقيد. فمثلاً، يطلب نمط "المنافذ والمحوّلات" أن تفصل شيفرة مجالك عن أي شيء يتعلق بالتعقيد العَرَضي؛ وتعيش تلك الشيفرة في مجلد "adapters".

### جعل التغيير سهلاً

أحياناً يكون من المنطقي إجراء بعض إعادة الهيكلة _قبل_ إجراء التغيير.

> اجعل التغيير سهلاً أولاً، ثم أجرِ التغيير السهل

~كينت بيك

لهذا السبب، لننقل شيفرة `http`، أي `driver.go` و`handler.go`، إلى حزمة (package) باسم `httpserver` داخل مجلد `adapters`، ونغيّر اسمي حزمتيهما إلى `httpserver`.

ستحتاج الآن إلى استيراد الحزمة الجذرية في `handler.go` للإشارة إلى الطريقة `Greet`...

```go
package httpserver

import (
	"fmt"
	"net/http"

	go_specs_greet "github.com/quii/go-specs-greet/domain/interactions"
)

func Handler(w http.ResponseWriter, r *http.Request) {
	name := r.URL.Query().Get("name")
	fmt.Fprint(w, go_specs_greet.Greet(name))
}

```

واستورد المحوّل `httpserver` في `main.go`:

```go
package main

import (
	"net/http"

	"github.com/quii/go-specs-greet/adapters/httpserver"
)

func main() {
	handler := http.HandlerFunc(httpserver.Handler)
	http.ListenAndServe(":8080", handler)
}
```

وحدّث الاستيراد والإشارة إلى `Driver` في `greeter_server_test.go`:

```go
driver := httpserver.Driver{BaseURL: "http://localhost:8080", Client: &client}
```

وأخيراً، من المفيد تجميع شيفرتنا على مستوى المجال في مجلدها الخاص أيضاً. لا تتكاسل فيكون في مشاريعك مجلد `domain` فيه مئات الأنواع والدوال غير المترابطة. ابذل جهداً في التفكير في مجالك، واجمع معاً الأفكار التي تنتمي بعضها إلى بعض. فهذا سيجعل مشروعك أسهل فهماً، وسيحسّن جودة استيراداتك.

فبدلاً من رؤية

```go
domain.Greet
```

وهو غريب بعض الشيء، فضّل بدلاً من ذلك

```go
interactions.Greet
```

أنشئ مجلد `domain` ليضم كل شيفرة مجالك، وداخله مجلد `interactions`. وبحسب أدواتك، قد تحتاج إلى تحديث بعض الاستيرادات والشيفرة.

ينبغي أن تبدو شجرة مشروعنا الآن هكذا:

```
quii@Chriss-MacBook-Pro go-specs-greet % tree
.
├── Makefile
├── README.md
├── adapters
│   └── httpserver
│       ├── driver.go
│       └── handler.go
├── cmd
│   └── httpserver
|       ├── Dockerfile
│       ├── greeter_server_test.go
│       └── main.go
├── domain
│   └── interactions
│       ├── greet.go
│       └── greet_test.go
├── go.mod
├── go.sum
└── specifications
    └── adapters.go
    └── greet.go

```

شيفرة مجالنا، أي **التعقيد الجوهري**، تعيش في جذر الوحدة النمطية لغو، والشيفرة التي ستتيح لنا استعمالها في "العالم الحقيقي" منظمة في **محوّلات**. والمجلد `cmd` هو المكان الذي نستطيع فيه تركيب هذه التجميعات المنطقية في تطبيقات عملية، لها اختبارات صندوق أسود تتحقق من أن كل شيء يعمل. رائع!

وأخيراً، يمكننا إجراء قدر _ضئيل_ من الترتيب في اختبار القبول. فإن نظرت في الخطوات عالية المستوى لاختبار القبول:

- ابنِ صورة Docker
- انتظر حتى تستمع على منفذ _ما_
- أنشئ مشغّلاً يفهم كيف يترجم اللغة الخاصة بالمجال إلى استدعاءات خاصة بالنظام
- وصّل المشغّل بالمواصفة

... فستدرك أن لدينا المتطلبات نفسها لاختبار قبول خادم gRPC أيضاً!

يبدو المجلد `adapters` مكاناً مناسباً كأي مكان آخر، لذا غلّف الخطوتين الأوليين داخل ملف باسم `docker.go` في دالة (function) سنعيد استعمالها لاحقاً.

```go
package adapters

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/alecthomas/assert/v2"
	"github.com/docker/go-connections/nat"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"
)

func StartDockerServer(
	t testing.TB,
	port string,
	dockerFilePath string,
) {
	ctx := context.Background()
	t.Helper()
	req := testcontainers.ContainerRequest{
		FromDockerfile: testcontainers.FromDockerfile{
			Context:       "../../.",
			Dockerfile:    dockerFilePath,
			PrintBuildLog: true,
		},
		ExposedPorts: []string{fmt.Sprintf("%s:%s", port, port)},
		WaitingFor:   wait.ForListeningPort(nat.Port(port)).WithStartupTimeout(5 * time.Second),
	}
	container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: req,
		Started:          true,
	})
	assert.NoError(t, err)
	t.Cleanup(func() {
		assert.NoError(t, container.Terminate(ctx))
	})
}
```

وهذا يمنحنا فرصة لتنظيف اختبار القبول قليلاً

```go
func TestGreeterServer(t *testing.T) {
	var (
		port           = "8080"
		dockerFilePath = "./cmd/httpserver/Dockerfile"
		baseURL        = fmt.Sprintf("http://localhost:%s", port)
		driver         = httpserver.Driver{BaseURL: baseURL, Client: &http.Client{
			Timeout: 1 * time.Second,
		}}
	)

	adapters.StartDockerServer(t, port, dockerFilePath)
	specifications.GreetSpecification(t, driver)
}
```

ينبغي أن يجعل هذا كتابة الاختبار _التالي_ أبسط.

## اكتب الاختبار أولاً

يمكن تحقيق هذه الوظيفة الجديدة بإنشاء `adapter` جديد للتفاعل مع شيفرة مجالنا. ولهذا السبب:

- لا ينبغي أن نضطر إلى تغيير المواصفة؛
- ينبغي أن نستطيع إعادة استعمال المواصفة؛
- ينبغي أن نستطيع إعادة استعمال شيفرة المجال.

أنشئ مجلداً جديداً `grpcserver` داخل `cmd` ليضم برنامجنا الجديد واختبار القبول المقابل له. وداخل `cmd/grpc_server/greeter_server_test.go`، أضف اختبار قبول يشبه كثيراً اختبار خادم HTTP، لا مصادفة بل عن قصد.

```go
package main_test

import (
	"fmt"
	"testing"

	"github.com/quii/go-specs-greet/adapters"
	"github.com/quii/go-specs-greet/adapters/grpcserver"
	"github.com/quii/go-specs-greet/specifications"
)

func TestGreeterServer(t *testing.T) {
	var (
		port           = "50051"
		dockerFilePath = "./cmd/grpcserver/Dockerfile"
		driver         = grpcserver.Driver{Addr: fmt.Sprintf("localhost:%s", port)}
	)

	adapters.StartDockerServer(t, port, dockerFilePath)
	specifications.GreetSpecification(t, &driver)
}
```

الفروق الوحيدة هي:

- نستعمل ملف Docker مختلفاً، لأننا نبني برنامجاً مختلفاً
- وهذا يعني أننا سنحتاج إلى `Driver` جديد يستعمل `gRPC` للتفاعل مع برنامجنا الجديد

## حاول تشغيل الاختبار

```
./greeter_server_test.go:26:12: undefined: grpcserver
```

لم ننشئ `Driver` بعد، لذا لن يُصرَّف.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

أنشئ مجلد `grpcserver` داخل `adapters` وأنشئ داخله `driver.go`

```go
package grpcserver

type Driver struct {
	Addr string
}

func (d Driver) Greet(name string) (string, error) {
	return "", nil
}
```

إن شغّلته مجدداً فينبغي أن _يُصرَّف_ الآن لكنه لا ينجح، لأننا لم ننشئ `Dockerfile` والبرنامج المقابل لتشغيله.

أنشئ `Dockerfile` جديداً داخل `cmd/grpcserver`.

```dockerfile
# Make sure to specify the same Go version as the one in the go.mod file.
FROM golang:1.18-alpine

WORKDIR /app

COPY go.mod ./

RUN go mod download

COPY . .

RUN go build -o svr cmd/grpcserver/*.go

EXPOSE 50051
CMD [ "./svr" ]
```

و`main.go`

```go
package main

import "fmt"

func main() {
	fmt.Println("implement me")
}
```

ينبغي أن تجد الآن أن الاختبار يفشل لأن خادمنا لا يستمع على المنفذ. وحان الآن وقت استعمال gRPC لبدء بناء العميل والخادم.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

### إطار gRPC

إن لم تكن مألوفاً مع gRPC، فأنصحك بالبدء بإلقاء نظرة على [موقع gRPC](https://grpc.io). ومع ذلك، فهو في هذا الفصل مجرد نوع آخر من المحوّلات إلى نظامنا، أي وسيلة لأنظمة أخرى لاستدعاء (**ا**ستدعاء **إ**جراء **ب**عيد، أي remote procedure call) شيفرة مجالنا الممتازة.

والحيلة أنك تعرّف "تعريف خدمة" باستعمال Protocol Buffers، ثم تولّد شيفرة الخادم والعميل من التعريف. وهذا لا يعمل مع غو فحسب، بل مع معظم اللغات الشائعة أيضاً. وهذا يعني أنك تستطيع مشاركة تعريف مع فرق أخرى في شركتك قد لا تكتب بغو أصلاً، ويظل التواصل بين الخدمات سلساً.

إن لم تكن قد استعملت gRPC من قبل، فستحتاج إلى تثبيت **مصرِّف Protocol buffer** وبعض **إضافات غو**. [وفي موقع gRPC تعليمات واضحة عن كيفية فعل ذلك](https://grpc.io/docs/languages/go/quickstart/).

داخل المجلد نفسه الذي فيه مشغّلنا الجديد، أضف ملف `greet.proto` بما يلي

```protobuf
syntax = "proto3";

option go_package = "github.com/quii/adapters/grpcserver";

package grpcserver;

service Greeter {
  rpc Greet (GreetRequest) returns (GreetReply) {}
}

message GreetRequest {
  string name = 1;
}

message GreetReply {
  string message = 1;
}
```

لفهم هذا التعريف، لا تحتاج إلى أن تكون خبيراً في Protocol Buffers. فنحن نعرّف خدمة لها طريقة `Greet`، ثم نصف أنواع الرسائل الواردة والصادرة.

داخل `adapters/grpcserver` شغّل ما يلي لتوليد شيفرة العميل والخادم

```
protoc --go_out=. --go_opt=paths=source_relative \
    --go-grpc_out=. --go-grpc_opt=paths=source_relative \
    greet.proto
```

إن نجح ذلك، فستكون لدينا شيفرة مولّدة لنستعملها. لنبدأ باستعمال شيفرة العميل المولّدة داخل `Driver`.

```go
package grpcserver

import (
	"context"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type Driver struct {
	Addr string
}

func (d Driver) Greet(name string) (string, error) {
	//todo: we shouldn't redial every time we call greet, refactor out when we're green
	conn, err := grpc.Dial(d.Addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return "", err
	}
	defer conn.Close()

	client := NewGreeterClient(conn)
	greeting, err := client.Greet(context.Background(), &GreetRequest{
		Name: name,
	})
	if err != nil {
		return "", err
	}

	return greeting.Message, nil
}
```

والآن بعد أن صار لدينا عميل، علينا تحديث `main.go` لإنشاء خادم. وتذكّر أننا في هذه المرحلة نحاول فقط جعل اختبارنا ينجح، ولا نقلق بشأن جودة الشيفرة.

```go
package main

import (
	"context"
	"log"
	"net"

	"github.com/quii/go-specs-greet/adapters/grpcserver"
	"google.golang.org/grpc"
)

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatal(err)
	}
	s := grpc.NewServer()
	grpcserver.RegisterGreeterServer(s, &GreetServer{})

	if err := s.Serve(lis); err != nil {
		log.Fatal(err)
	}
}

type GreetServer struct {
	grpcserver.UnimplementedGreeterServer
}

func (g GreetServer) Greet(ctx context.Context, request *grpcserver.GreetRequest) (*grpcserver.GreetReply, error) {
	return &grpcserver.GreetReply{Message: "fixme"}, nil
}
```

لإنشاء خادم gRPC، علينا تحقيق الواجهة التي ولّدها لنا

```go
// GreeterServer is the server API for Greeter service.
// All implementations must embed UnimplementedGreeterServer
// for forward compatibility
type GreeterServer interface {
	Greet(context.Context, *GreetRequest) (*GreetReply, error)
	mustEmbedUnimplementedGreeterServer()
}
```

الدالة `main` لدينا:

- تستمع على منفذ
- تنشئ `GreetServer` يحقق الواجهة، ثم تسجّله باستعمال `grpcServer.RegisterGreeterServer`، مع `grpc.Server`.
- تستعمل الخادم مع المستمع

لن يكون جهداً إضافياً كبيراً أن نستدعي شيفرة مجالنا داخل `greetServer.Greet` بدلاً من تثبيت `fix-me` في الرسالة، لكنني أود تشغيل اختبار القبول أولاً لأرى إن كان كل شيء يعمل على مستوى النقل، وأتحقق من مخرجات الاختبار الفاشل.

```
greet.go:16: Expected values to be equal:
-fixme
\ No newline at end of file
+Hello, Mike
\ No newline at end of file
```

رائع! نرى أن مشغّلنا يستطيع الاتصال بخادم gRPC في الاختبار.

والآن، استدعِ شيفرة مجالنا داخل `GreetServer`

```go
type GreetServer struct {
	grpcserver.UnimplementedGreeterServer
}

func (g GreetServer) Greet(ctx context.Context, request *grpcserver.GreetRequest) (*grpcserver.GreetReply, error) {
	return &grpcserver.GreetReply{Message: interactions.Greet(request.Name)}, nil
}
```

أخيراً، ينجح! لدينا اختبار قبول يثبت أن خادم التحية عبر gRPC يتصرف كما نريد.

## أعد الهيكلة

ارتكبنا عدة خطايا لجعل الاختبار ينجح، لكن الآن وقد نجحت الاختبارات، صارت لدينا شبكة الأمان لإعادة الهيكلة.

### بسّط `main`

كما في السابق، لا نريد أن يحتوي `main` على شيفرة كثيرة. يمكننا نقل `GreetServer` الجديد إلى `adapters/grpcserver` لأن ذلك هو مكانه الطبيعي. ومن حيث التماسك، إن غيّرنا تعريف الخدمة، فإننا نريد أن يقتصر "نطاق انفجار" التغيير على تلك المنطقة من شيفرتنا.

### لا تُعِد الاتصال في المشغّل في كل مرة

لدينا اختبار واحد فقط، لكن إن وسّعنا مواصفتنا (وسنفعل)، فليس من المنطقي أن يعيد المشغّل الاتصال مع كل استدعاء RPC جديد.

```go
package grpcserver

import (
	"context"
	"sync"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type Driver struct {
	Addr string

	connectionOnce sync.Once
	conn           *grpc.ClientConn
	client         GreeterClient
}

func (d *Driver) Greet(name string) (string, error) {
	client, err := d.getClient()
	if err != nil {
		return "", err
	}

	greeting, err := client.Greet(context.Background(), &GreetRequest{
		Name: name,
	})
	if err != nil {
		return "", err
	}

	return greeting.Message, nil
}

func (d *Driver) getClient() (GreeterClient, error) {
	var err error
	d.connectionOnce.Do(func() {
		d.conn, err = grpc.Dial(d.Addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
		d.client = NewGreeterClient(d.conn)
	})
	return d.client, err
}
```

نبيّن هنا كيف يمكننا استعمال [`sync.Once`](https://pkg.go.dev/sync#Once) لضمان ألا يحاول `Driver` إنشاء اتصال بخادمنا إلا مرة واحدة.

لنلقِ نظرة على الحالة الحالية لبنية مشروعنا قبل المتابعة.

```
quii@Chriss-MacBook-Pro go-specs-greet % tree
.
├── Makefile
├── README.md
├── adapters
│   ├── docker.go
│   ├── grpcserver
│   │   ├── driver.go
│   │   ├── greet.pb.go
│   │   ├── greet.proto
│   │   ├── greet_grpc.pb.go
│   │   └── server.go
│   └── httpserver
│       ├── driver.go
│       └── handler.go
├── cmd
│   ├── grpcserver
│   │   ├── Dockerfile
│   │   ├── greeter_server_test.go
│   │   └── main.go
│   └── httpserver
│       ├── Dockerfile
│       ├── greeter_server_test.go
│       └── main.go
├── domain
│   └── interactions
│       ├── greet.go
│       └── greet_test.go
├── go.mod
├── go.sum
└── specifications
    └── greet.go
```

- يضم المجلد `adapters` وحدات متماسكة من الوظائف مجمّعة معاً
- يضم المجلد `cmd` تطبيقاتنا واختبارات القبول المقابلة لها
- شيفرتنا منفصلة تماماً عن أي تعقيد عَرَضي

### توحيد `Dockerfile`

لعلك لاحظت أن ملفي `Dockerfiles` متطابقان تقريباً باستثناء مسار الملف التنفيذي الذي نريد بناءه.

يمكن لملفات `Dockerfiles` أن تقبل وسطاء تتيح لنا إعادة استعمالها في سياقات مختلفة، وهذا يبدو مثالياً. يمكننا حذف ملفي Docker وأن يكون لدينا بدلاً منهما ملف واحد في جذر المشروع بما يلي

```dockerfile
# Make sure to specify the same Go version as the one in the go.mod file.
FROM golang:1.18-alpine

WORKDIR /app

ARG bin_to_build

COPY go.mod ./

RUN go mod download

COPY . .

RUN go build -o svr cmd/${bin_to_build}/main.go

CMD [ "./svr" ]
```

سنضطر إلى تحديث الدالة `StartDockerServer` لتمرير الوسيط حين نبني الصور

```go
func StartDockerServer(
	t testing.TB,
	port string,
	binToBuild string,
) {
	ctx := context.Background()
	t.Helper()
	req := testcontainers.ContainerRequest{
		FromDockerfile: testcontainers.FromDockerfile{
			Context:    "../../.",
			Dockerfile: "Dockerfile",
			BuildArgs: map[string]*string{
				"bin_to_build": &binToBuild,
			},
			PrintBuildLog: true,
		},
		ExposedPorts: []string{fmt.Sprintf("%s:%s", port, port)},
		WaitingFor:   wait.ForListeningPort(nat.Port(port)).WithStartupTimeout(5 * time.Second),
	}
	container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: req,
		Started:          true,
	})
	assert.NoError(t, err)
	t.Cleanup(func() {
		assert.NoError(t, container.Terminate(ctx))
	})
}
```

وأخيراً، حدّث اختباراتنا لتمرير الصورة المراد بناؤها (افعل هذا للاختبار الآخر وغيّر `grpcserver` إلى `httpserver`).

```go
func TestGreeterServer(t *testing.T) {
	var (
		port   = "50051"
		driver = grpcserver.Driver{Addr: fmt.Sprintf("localhost:%s", port)}
	)

	adapters.StartDockerServer(t, port, "grpcserver")
	specifications.GreetSpecification(t, &driver)
}
```

### فصل الأنواع المختلفة من الاختبارات

اختبارات القبول رائعة من حيث إنها تختبر أن النظام كله يعمل من منظور سلوكي خالص يواجه المستخدم، لكن لها عيوبها مقارنة باختبارات الوحدة:

- أبطأ
- جودة التغذية الراجعة كثيراً ما تكون أقل تركيزاً من اختبار الوحدة
- لا تساعدك في الجودة الداخلية أو التصميم

يرشدنا [هرم الاختبارات](https://martinfowler.com/articles/practical-test-pyramid.html) إلى نوع المزيج الذي نريده في مجموعة اختباراتنا، وينبغي أن تقرأ مقال فاولر لمزيد من التفاصيل، لكن الملخص المبسّط جداً لهذا الفصل هو "كثير من اختبارات الوحدة وقليل من اختبارات القبول".

ولهذا السبب، مع نمو المشروع قد تجد نفسك كثيراً في مواقف تستغرق فيها اختبارات القبول بضع دقائق لتعمل. ولتقديم تجربة ودية للمطورين الذين ينزّلون مشروعك، يمكنك تمكين المطورين من تشغيل الأنواع المختلفة من الاختبارات بشكل منفصل.

يُفضَّل أن يكون تشغيل `go test ./...` ممكناً دون أي إعداد إضافي من المهندس، باستثناء بعض التبعيات الأساسية، كمصرِّف غو (بالطبع) وربما Docker أيضاً.

توفر غو آلية للمهندسين لتشغيل الاختبارات "القصيرة" فقط بـ[الراية short](https://pkg.go.dev/testing#Short)

`go test -short ./...`

يمكننا الإضافة إلى اختبارات القبول للتحقق مما إذا كان المستخدم يريد تشغيلها، بفحص قيمة الراية

```go
if testing.Short() {
	t.Skip()
}
```

أنشأت `Makefile` لبيان هذا الاستعمال

```makefile
build:
	golangci-lint run
	go test ./...

unit-tests:
	go test -short ./...
```

### متى ينبغي أن أكتب اختبارات القبول؟

أفضل ممارسة هي تفضيل وجود كثير من اختبارات الوحدة السريعة وقليل من اختبارات القبول، لكن كيف تقرر متى تكتب اختبار قبول مقابل اختبارات الوحدة؟

من الصعب إعطاء قاعدة ملموسة، لكن الأسئلة التي أطرحها على نفسي عادةً هي:

- هل هذه حالة حدّية؟ أفضّل اختبار هذه الحالات باختبارات الوحدة
- هل هذا شيء يتحدث عنه غير المختصين بالحواسيب كثيراً؟ عندها أفضّل أن تكون لدي ثقة كبيرة بأن الشيء الأساسي يعمل "حقاً"، لذا أضيف اختبار قبول
- هل أصف رحلة مستخدم، لا دالة محددة؟ اختبار قبول
- هل ستمنحني اختبارات الوحدة ثقة كافية؟ أحياناً تأخذ رحلة موجودة لها اختبار قبول بالفعل، لكنك تضيف وظائف أخرى للتعامل مع سيناريوهات مختلفة بسبب مدخلات مختلفة. وفي هذه الحالة، إضافة اختبار قبول آخر تضيف تكلفة لكنها تجلب قيمة قليلة، لذا أفضّل بعض اختبارات الوحدة.

## التقدم في عملنا

مع كل هذا الجهد، تأمل أن يكون توسيع نظامنا بسيطاً الآن. صنع نظام بسيط للعمل عليه ليس بالضرورة سهلاً، لكنه يستحق الوقت، وهو أسهل بكثير حين تبدأ مشروعاً.

لنوسّع واجهتنا البرمجية لتتضمن وظيفة "اللعن".

## اكتب الاختبار أولاً

هذا سلوك جديد كلياً، لذا ينبغي أن نبدأ باختبار قبول. أضف ما يلي في ملف المواصفة

```go
type MeanGreeter interface {
	Curse(name string) (string, error)
}

func CurseSpecification(t *testing.T, meany MeanGreeter) {
	got, err := meany.Curse("Chris")
	assert.NoError(t, err)
	assert.Equal(t, got, "Go to hell, Chris!")
}
```

اختر أحد اختبارات القبول وحاول استعمال المواصفة

```go
func TestGreeterServer(t *testing.T) {
	if testing.Short() {
		t.Skip()
	}
	var (
		port   = "50051"
		driver = grpcserver.Driver{Addr: fmt.Sprintf("localhost:%s", port)}
	)

	t.Cleanup(driver.Close)
	adapters.StartDockerServer(t, port, "grpcserver")
	specifications.GreetSpecification(t, &driver)
	specifications.CurseSpecification(t, &driver)
}
```

## حاول تشغيل الاختبار

```
# github.com/quii/go-specs-greet/cmd/grpcserver_test [github.com/quii/go-specs-greet/cmd/grpcserver.test]
./greeter_server_test.go:27:39: cannot use &driver (value of type *grpcserver.Driver) as type specifications.MeanGreeter in argument to specifications.CurseSpecification:
	*grpcserver.Driver does not implement specifications.MeanGreeter (missing Curse method)
```

`Driver` لا يدعم `Curse` بعد.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

تذكّر أننا نحاول فقط جعل الاختبار يعمل، لذا أضف الطريقة إلى `Driver`

```go
func (d *Driver) Curse(name string) (string, error) {
	return "", nil
}
```

إن حاولت مجدداً، فينبغي أن يُصرَّف الاختبار ويعمل ويفشل

```
greet.go:26: Expected values to be equal:
+Go to hell, Chris!
\ No newline at end of file
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

سنحتاج إلى تحديث مواصفة Protocol Buffer لتحتوي على طريقة `Curse`، ثم إعادة توليد شيفرتنا.

```protobuf
service Greeter {
  rpc Greet (GreetRequest) returns (GreetReply) {}
  rpc Curse (GreetRequest) returns (GreetReply) {}
}
```

قد تقول إن إعادة استعمال النوعين `GreetRequest` و`GreetReply` اقتران غير مناسب، لكن يمكننا معالجة ذلك في مرحلة إعادة الهيكلة. وكما أشدد دائماً، نحن نحاول فقط جعل الاختبار ينجح كي نتحقق من أن البرنامج يعمل، _ثم_ نجعله جميلاً.

أعد توليد شيفرتنا بما يلي (داخل `adapters/grpcserver`).

```
protoc --go_out=. --go_opt=paths=source_relative \
    --go-grpc_out=. --go-grpc_opt=paths=source_relative \
    greet.proto
```

### تحديث المشغّل

والآن بعد تحديث شيفرة العميل، يمكننا استدعاء `Curse` في `Driver`

```go
func (d *Driver) Curse(name string) (string, error) {
	client, err := d.getClient()
	if err != nil {
		return "", err
	}

	greeting, err := client.Curse(context.Background(), &GreetRequest{
		Name: name,
	})
	if err != nil {
		return "", err
	}

	return greeting.Message, nil
}
```

### تحديث الخادم

وأخيراً، علينا إضافة الطريقة `Curse` إلى `Server`

```go
package grpcserver

import (
	"context"
	"fmt"

	"github.com/quii/go-specs-greet/domain/interactions"
)

type GreetServer struct {
	UnimplementedGreeterServer
}

func (g GreetServer) Curse(ctx context.Context, request *GreetRequest) (*GreetReply, error) {
	return &GreetReply{Message: fmt.Sprintf("Go to hell, %s!", request.Name)}, nil
}

func (g GreetServer) Greet(ctx context.Context, request *GreetRequest) (*GreetReply, error) {
	return &GreetReply{Message: interactions.Greet(request.Name)}, nil
}
```

ينبغي أن تنجح الاختبارات الآن.

## أعد الهيكلة

جرّب فعل هذا بنفسك.

- استخرج "منطق المجال" الخاص بـ`Curse` بعيداً عن خادم gRPC، كما فعلنا مع `Greet`. واستعمل المواصفة كاختبار وحدة على منطق مجالك
- استعمل أنواعاً مختلفة في protobuf لضمان أن أنواع رسائل `Greet` و`Curse` منفصلة.

## تنفيذ `Curse` لخادم HTTP

مرة أخرى، هذا تمرين لك أيها القارئ. فلدينا مواصفتنا على مستوى المجال ومنطقنا على مستوى المجال مفصولين بشكل أنيق. وإن كنت قد تابعت هذا الفصل، فينبغي أن يكون هذا مباشراً جداً.

- أضف المواصفة إلى اختبار القبول الموجود لخادم HTTP
- حدّث `Driver`
- أضف نقطة النهاية الجديدة إلى الخادم، وأعد استعمال شيفرة المجال لتنفيذ الوظيفة. وقد ترغب في استعمال `http.NewServeMux` لمعالجة التوجيه إلى نقاط النهاية المنفصلة.

تذكّر أن تعمل بخطوات صغيرة، وأن تودع وتشغّل اختباراتك كثيراً. وإن علقت حقاً [فيمكنك إيجاد تنفيذي على GitHub](https://github.com/quii/go-specs-greet).

## حسّن النظامين كليهما بتحديث منطق المجال باختبار وحدة

كما ذكرنا، ليس كل تغيير في النظام ينبغي أن يُقاد عبر اختبار قبول. فتبديلات قواعد الأعمال والحالات الحدّية ينبغي أن تكون قيادتها عبر اختبار وحدة بسيطة إن كنت قد فصلت الاهتمامات جيداً.

أضف اختبار وحدة للدالة `Greet` يجعل `name` افتراضياً `World` إن كان فارغاً. وينبغي أن ترى مدى بساطة ذلك، ثم تنعكس قواعد الأعمال في التطبيقين كليهما "مجاناً".

## الخلاصة

بناء أنظمة بتكلفة تغيير معقولة يتطلب أن تكون لديك اختبارات قبول مصممة لتساعدك، لا لتصبح عبئاً في الصيانة. ويمكن استعمالها وسيلة للتوجيه، أو كما يقول كتاب GOOS، "لإنماء" برمجياتك بمنهجية.

أرجو أن ترى بهذا المثال سير العمل المنظم والقابل للتنبؤ في تطبيقنا لقيادة التغيير، وكيف يمكنك استعماله في عملك.

يمكنك أن تتخيل التحدث مع صاحب مصلحة يريد توسيع النظام الذي تعمل عليه بطريقة ما. جسّد ذلك في مواصفة بطريقة تتمحور حول المجال ولا تعتمد على التنفيذ، واستعملها نجم شمال لجهودك. وقد وصفنا أنا وريا الاستفادة من أساليب BDD مثل "رسم خرائط الأمثلة" (Example Mapping) [في محاضرتنا في GopherconUK](https://www.youtube.com/watch?v=ZMWJCk_0WrY) لمساعدتك على فهم التعقيد الجوهري بعمق أكبر، وتمكينك من كتابة مواصفات أكثر تفصيلاً ومعنى.

فصل الاهتمامات بين التعقيد الجوهري والعَرَضي سيجعل عملك أقل ارتجالاً وأكثر تنظيماً وقصداً؛ وهذا يضمن صلابة اختبارات القبول ويساعدها على أن تكون عبئاً أقل في الصيانة.

يقدّم ديف فارلي نصيحة ممتازة:

> تخيّل أقل شخص تقني يخطر ببالك، ممن يفهمون مجال المشكلة، وهو يقرأ اختبارات القبول لديك. ينبغي أن تكون الاختبارات مفهومة لذلك الشخص.

ينبغي إذن أن تكون المواصفات توثيقاً في الوقت نفسه. فينبغي أن تحدد بوضوح كيف ينبغي أن يتصرف النظام. وهذه الفكرة هي المبدأ وراء أدوات مثل [Cucumber](https://cucumber.io)، التي توفر لك لغة خاصة بالمجال لتجسيد السلوك كشيفرة، ثم تحوّل تلك اللغة إلى استدعاءات للنظام، تماماً كما فعلنا هنا.

### ما تناولناه

- كتابة مواصفات مجردة تتيح لك التعبير عن التعقيد الجوهري للمشكلة التي تحلها وإزالة التعقيد العَرَضي. وهذا سيمكّنك من إعادة استعمال المواصفات في سياقات مختلفة.
- كيف تستعمل [Testcontainers](https://golang.testcontainers.org) لإدارة دورة حياة نظامك لاختبارات القبول. وهذا يتيح لك اختبار الصورة التي تنوي إطلاقها اختباراً شاملاً على حاسوبك، فيمنحك تغذية راجعة سريعة وثقة.
- مدخل موجز إلى وضع تطبيقك في حاوية باستعمال Docker
- إطار gRPC
- بدلاً من مطاردة بنى مجلدات جاهزة، يمكنك استعمال أسلوبك في التطوير لاستخلاص بنية تطبيقك بشكل طبيعي، بناءً على احتياجاتك الخاصة

### مواد إضافية

- في هذا المثال، لغتنا "الخاصة بالمجال" ليست لغة خاصة بالمجال بالمعنى الكامل؛ فقد استعملنا الواجهات فقط لفصل مواصفتنا عن العالم الحقيقي وتمكيننا من التعبير عن منطق المجال بنظافة. ومع نمو نظامك، قد يصبح هذا المستوى من التجريد مرتبكاً وغير واضح. [اقرأ عن "نمط السيناريو" (Screenplay Pattern)](https://cucumber.io/blog/bdd/understanding-screenplay-part-1/) إن أردت مزيداً من الأفكار عن كيفية بناء مواصفاتك.
- للتأكيد، كتاب [Growing Object-Oriented Software, Guided by Tests](http://www.growing-object-oriented-software.com) كتاب كلاسيكي. فهو يبيّن تطبيق أسلوب "مدرسة لندن" "من الأعلى إلى الأسفل" في كتابة البرمجيات. وكل من استمتع بكتاب "تعلّم غو بالاختبارات" ينبغي أن يجني قيمة كبيرة من قراءة GOOS.
- [في مستودع الشيفرة النموذجية](https://github.com/quii/go-specs-greet) شيفرة وأفكار أخرى لم أكتب عنها هنا، مثل بناء Docker متعدد المراحل، وقد ترغب في الاطلاع عليها.
  - وتحديداً، *للمتعة*، صنعت **برنامجاً ثالثاً**، وهو موقع ويب فيه بعض نماذج HTML لـ`Greet` و`Curse`. ويستفيد `Driver` من الوحدة الممتازة [https://github.com/go-rod/rod](https://github.com/go-rod/rod)، التي تتيح له العمل مع الموقع بمتصفح، تماماً كما يفعل المستخدم. وبالنظر إلى سجل git، يمكنك أن ترى كيف بدأت دون استعمال أي أدوات قوالب "لمجرد أن يعمل"، ثم بمجرد أن نجح اختبار القبول، صارت لدي حرية فعل ذلك دون خوف من إفساد الأشياء. -->
