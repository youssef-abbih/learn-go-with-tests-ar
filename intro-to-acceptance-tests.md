# مدخل إلى اختبارات القبول

في `$WORK`، صرنا نواجه الحاجة إلى "إيقاف لطيف" لخدماتنا. فالإيقاف اللطيف يضمن أن ينهي نظامك عمله كما ينبغي قبل أن يُنهى. والتشبيه من العالم الحقيقي هو شخص يحاول إنهاء مكالمة هاتفية بشكل لائق قبل الانتقال إلى اجتماعه التالي، بدلاً من أن يغلق الخط في منتصف الجملة.

سيقدّم هذا الفصل مدخلاً إلى الإيقاف اللطيف في سياق خادم HTTP، وإلى كيفية كتابة "اختبارات القبول" (acceptance tests) لتمنح نفسك الثقة في سلوك شيفرتك (code).

وبعد قراءته ستعرف كيف تشارك حزماً (packages) ذات اختبارات ممتازة، وتقلل جهود الصيانة، وتزيد الثقة في جودة عملك.

## ما يكفي من المعلومات عن Kubernetes

نشغّل برمجياتنا على [Kubernetes](https://kubernetes.io/) (K8s). وسيُنهي K8s "الحاويات المجمّعة" (pods)، أي برمجياتنا عملياً، لأسباب مختلفة، ومن أشيعها حين ندفع شيفرة جديدة نريد نشرها.

نضع لأنفسنا معايير عالية فيما يخص [مقاييس DORA](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)، لذا نعمل بطريقة ننشر فيها تحسينات وميزات صغيرة تدريجية إلى بيئة الإنتاج عدة مرات في اليوم.

حين يريد k8s إنهاء حاوية مجمّعة، فإنه يبدأ ["دورة حياة الإنهاء"](https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-terminating-with-grace)، ومن أجزائها إرسال إشارة `SIGTERM` إلى برنامجنا. وهذا هو k8s يقول لشيفرتنا:

> عليك أن توقف نفسك، وتنهي أي عمل تقوم به، لأنني بعد "مهلة سماح" معيّنة سأرسل `SIGKILL`، وعندها تنطفئ الأنوار بالنسبة إليك.

عند `SIGKILL` يتوقف فوراً أي عمل قد يكون برنامجك يقوم به.

## إن لم يكن لديك لطف

بحسب طبيعة برنامجك، إن تجاهلت `SIGTERM` فقد تواجه مشكلات.

كانت مشكلتنا تحديداً مع طلبات HTTP قيد التنفيذ. فحين كان اختبار (test) آلي يختبر واجهتنا البرمجية، إن قرر k8s إيقاف الحاوية المجمّعة، فسيموت الخادم، ولن يحصل الاختبار على استجابة من الخادم، فيفشل الاختبار.

وهذا كان يُطلق تنبيهاً في قناة الحوادث لدينا، مما يتطلب من أحد المطورين أن يوقف ما يفعله ويعالج المشكلة. وحالات الفشل المتقطعة هذه مصدر إلهاء مزعج لفريقنا.

وهذه المشكلات ليست مقتصرة على اختباراتنا. فإن أرسل مستخدم طلباً إلى نظامك وأُنهيت العملية في منتصف الطريق، فالأرجح أن يستقبله خطأ HTTP من الفئة 5xx، وهذه ليست تجربة المستخدم التي تريد تقديمها.

## حين يكون لديك لطف

ما نريد فعله هو الاستماع إلى `SIGTERM`، وبدلاً من قتل الخادم فوراً، نريد:

- التوقف عن الاستماع إلى أي طلبات أخرى
- السماح لأي طلبات قيد التنفيذ بأن تنتهي
- *ثم* إنهاء العملية

## كيف يكون لديك لطف

لحسن الحظ، لدى غو (Go) بالفعل آلية لإيقاف الخادم بلطف هي [net/http/Server.Shutdown](https://pkg.go.dev/net/http#Server.Shutdown).

> تُوقف `Shutdown` الخادم بلطف دون مقاطعة أي اتصالات نشطة. وتعمل `Shutdown` بإغلاق كل المستمعين المفتوحين أولاً، ثم إغلاق كل الاتصالات الخاملة، ثم الانتظار إلى أجل غير مسمى حتى تعود الاتصالات إلى الخمول، ثم الإيقاف. وإن انتهت صلاحية السياق المقدّم قبل اكتمال الإيقاف، تعيد `Shutdown` خطأ السياق، وإلا فإنها تعيد أي خطأ ناتج عن إغلاق المستمع أو المستمعين الأساسيين للخادم.

لمعالجة `SIGTERM` يمكننا استعمال [os/signal.Notify](https://pkg.go.dev/os/signal#Notify)، التي ترسل أي إشارات واردة إلى قناة نقدّمها.

وباستعمال هاتين الميزتين من المكتبة القياسية، يمكنك الاستماع إلى `SIGTERM` والإيقاف بلطف.

## حزمة الإيقاف اللطيف

لهذا الغرض، كتبت [https://pkg.go.dev/github.com/quii/go-graceful-shutdown](https://pkg.go.dev/github.com/quii/go-graceful-shutdown). وهي توفر دالة (function) مزخرِفة لـ`*http.Server` تستدعي طريقته (method) `Shutdown` حين تُكتشف إشارة `SIGTERM`

```go
func main() {
	var (
		ctx        = context.Background()
		httpServer = &http.Server{Addr: ":8080", Handler: http.HandlerFunc(acceptancetests.SlowHandler)}
		server     = gracefulshutdown.NewServer(httpServer)
	)

	if err := server.ListenAndServe(ctx); err != nil {
		// this will typically happen if our responses aren't written before the ctx deadline, not much can be done
		log.Fatalf("uh oh, didn't shutdown gracefully, some responses may have been lost %v", err)
	}

	// hopefully, you'll always see this instead
	log.Println("shutdown gracefully! all responses were sent")
}
```

تفاصيل الشيفرة ليست مهمة جداً لهذه القراءة، لكن يستحق الأمر إلقاء نظرة سريعة عليها قبل المتابعة.

## الاختبارات وحلقات التغذية الراجعة

حين كتبنا الحزمة `gracefulshutdown`، كانت لدينا اختبارات وحدة (unit tests) تثبت أنها تتصرف بشكل صحيح، مما منحنا الثقة لإعادة الهيكلة بجرأة. لكننا ما زلنا لم نشعر بـ"الثقة" في أنها تعمل **حقاً**.

أضفنا الحزمة `cmd` وصنعنا برنامجاً حقيقياً يستعمل الحزمة التي كنا نكتبها. وكنا نشغّله يدوياً، ونرسل إليه طلب HTTP، ثم نرسل `SIGTERM` لنرى ما سيحدث.

**ينبغي أن يشعر المهندس الذي بداخلك بعدم الارتياح تجاه الاختبار اليدوي**.
فهو ممل، ولا يتوسع، وغير دقيق، ومهدر للجهد. وإن كنت تكتب حزمة تنوي مشاركتها، وتريد أيضاً أن تبقيها بسيطة ورخيصة التغيير، فالاختبار اليدوي لن يفي بالغرض.

## اختبارات القبول

إن كنت قد قرأت بقية هذا الكتاب، فستكون قد كتبت في الغالب "اختبارات وحدة". واختبارات الوحدة أداة رائعة لتمكين إعادة الهيكلة دون خوف، ودفع التصميم المعياري الجيد، ومنع التراجعات، وتسهيل التغذية الراجعة (feedback) السريعة.

لكنها بطبيعتها لا تختبر إلا أجزاء صغيرة من نظامك. وعادةً لا تكون اختبارات
الوحدة وحدها *كافية* لاستراتيجية اختبار فعالة. تذكّر أننا نريد لأنظمتنا أن تكون **قابلة للإطلاق دائماً**. ولا يمكننا الاعتماد على الاختبار اليدوي، لذا نحتاج إلى نوع آخر من الاختبار: **اختبارات القبول**.

### ما هي؟

اختبارات القبول نوع من "اختبارات الصندوق الأسود". وتسمى أحياناً
"اختبارات وظيفية". وينبغي أن تختبر النظام كما يستعمله مستخدم النظام.

يشير مصطلح "الصندوق الأسود" إلى فكرة أن شيفرة الاختبار لا تصل إلى دواخل النظام، بل لا تستطيع إلا استعمال واجهته العامة وإجراء توكيدات (assertions) على السلوك الذي تلاحظه. وهذا يعني أنها لا تستطيع اختبار النظام إلا ككل.

وهذه صفة مفيدة، لأنها تعني أن الاختبارات تختبر النظام كما يفعل المستخدم، فلا تستطيع استعمال أي حلول التفافية خاصة قد تجعل الاختبار ينجح دون أن تثبت فعلاً ما تحتاج إلى إثباته. وهذا يشبه مبدأ تفضيل أن تعيش ملفات اختبارات الوحدة في حزمة اختبار منفصلة، مثل `package mypkg_test` بدلاً من `package mypkg`.

### فوائد اختبارات القبول

- حين تنجح، تعرف أن نظامك كله يتصرف كما تريد.
- هي أدق وأسرع وتتطلب جهداً أقل من الاختبار اليدوي.
- حين تُكتب جيداً، تكون توثيقاً دقيقاً ومتحققاً منه
  لنظامك، فلا تقع في فخ التوثيق الذي يبتعد عن السلوك الحقيقي للنظام.
- لا محاكاة! كل شيء حقيقي.

### عيوب محتملة مقارنة باختبارات الوحدة

- كتابتها مكلفة.
- تستغرق وقتاً أطول لتعمل.
- تعتمد على تصميم النظام.
- حين تفشل، لا تعطيك عادةً السبب الجذري، وقد يكون
  تنقيحها صعباً.
- لا تعطيك تغذية راجعة عن الجودة الداخلية لنظامك. فقد
  تكتب شيفرة رديئة تماماً وتجعل اختبار القبول ينجح مع ذلك.
- ليس عملياً اختبار كل السيناريوهات بسبب طبيعة الصندوق الأسود.

لهذا السبب، من الحماقة الاعتماد على اختبارات القبول وحدها. فليست لديها كثير من صفات اختبارات الوحدة، والنظام الذي فيه عدد كبير من اختبارات القبول يميل إلى المعاناة من تكاليف الصيانة ومن مهلة تسليم سيئة.

#### مهلة التسليم؟

تشير مهلة التسليم إلى المدة التي يستغرقها الإيداع (commit) من دمجه في
الفرع الرئيسي إلى نشره في بيئة الإنتاج. ويمكن أن يتراوح هذا الرقم من أسابيع بل أشهر لدى بعض الفرق إلى دقائق معدودة. ومرة أخرى، في `$WORK` نقدّر نتائج DORA ونريد إبقاء مهلة التسليم لدينا أقل من 10 دقائق.

نحتاج إلى أسلوب اختبار متوازن لنظام موثوق بمهلة
تسليم ممتازة، وعادةً ما يوصف هذا بمفهوم [هرم الاختبارات](https://martinfowler.com/articles/practical-test-pyramid.html).

## كيف تكتب اختبارات قبول أساسية

ما علاقة هذا بالمشكلة الأصلية؟ لقد كتبنا للتو حزمة هنا، ويمكن اختبارها بالكامل باختبارات الوحدة.

وكما ذكرت، لم تكن اختبارات الوحدة تمنحنا تماماً الثقة التي نحتاج إليها. فنحن نريد أن نتأكد *حقاً* من أن الحزمة تعمل حين تُدمج مع برنامج حقيقي قيد التشغيل. وينبغي أن نستطيع أتمتة الفحوص اليدوية التي كنا نجريها.

لنلقِ نظرة على برنامج الاختبار:

```go
func main() {
	var (
		ctx        = context.Background()
		httpServer = &http.Server{Addr: ":8080", Handler: http.HandlerFunc(acceptancetests.SlowHandler)}
		server     = gracefulshutdown.NewServer(httpServer)
	)

	if err := server.ListenAndServe(ctx); err != nil {
		// this will typically happen if our responses aren't written before the ctx deadline, not much can be done
		log.Fatalf("uh oh, didn't shutdown gracefully, some responses may have been lost %v", err)
	}

	// hopefully, you'll always see this instead
	log.Println("shutdown gracefully! all responses were sent")
}
```

لعلك خمّنت أن في `SlowHandler` استدعاء لـ`time.Sleep` لتأخير الاستجابة، كي يكون لدي وقت لإرسال `SIGTERM` ورؤية ما يحدث. والبقية شيفرة متكررة معتادة إلى حد بعيد:

- أنشئ `net/http/Server`؛
- غلّفه بالمكتبة (انظر: [نمط المزخرِف](https://en.wikipedia.org/wiki/Decorator_pattern))؛
- استعمل النسخة المغلَّفة لتنفيذ `ListenAndServe`.

### الخطوات عالية المستوى لاختبار القبول

- ابنِ البرنامج
- شغّله (وانتظر حتى يستمع على `8080`)
- أرسل طلب HTTP إلى الخادم
- قبل أن تسنح للخادم فرصة إرسال استجابة HTTP، أرسل `SIGTERM`
- تحقق مما إذا كنا ما زلنا نحصل على استجابة

### بناء البرنامج وتشغيله

```go
package acceptancetests

import (
	"fmt"
	"math/rand"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"time"
)

const (
	baseBinName = "temp-testbinary"
)

func LaunchTestProgram(port string) (cleanup func(), sendInterrupt func() error, err error) {
	binName, err := buildBinary()
	if err != nil {
		return nil, nil, err
	}

	sendInterrupt, kill, err := runServer(binName, port)

	cleanup = func() {
		if kill != nil {
			kill()
		}
		os.Remove(binName)
	}

	if err != nil {
		cleanup() // even though it's not listening correctly, the program could still be running
		return nil, nil, err
	}

	return cleanup, sendInterrupt, nil
}

func buildBinary() (string, error) {
	binName := randomString(10) + "-" + baseBinName

	build := exec.Command("go", "build", "-o", binName)

	if err := build.Run(); err != nil {
		return "", fmt.Errorf("cannot build tool %s: %s", binName, err)
	}
	return binName, nil
}

func runServer(binName string, port string) (sendInterrupt func() error, kill func(), err error) {
	dir, err := os.Getwd()
	if err != nil {
		return nil, nil, err
	}

	cmdPath := filepath.Join(dir, binName)

	cmd := exec.Command(cmdPath)

	if err := cmd.Start(); err != nil {
		return nil, nil, fmt.Errorf("cannot run temp converter: %s", err)
	}

	kill = func() {
		_ = cmd.Process.Kill()
	}

	sendInterrupt = func() error {
		return cmd.Process.Signal(syscall.SIGTERM)
	}

	err = waitForServerListening(port)

	return
}

func waitForServerListening(port string) error {
	for i := 0; i < 30; i++ {
		conn, _ := net.Dial("tcp", net.JoinHostPort("localhost", port))
		if conn != nil {
			conn.Close()
			return nil
		}
		time.Sleep(100 * time.Millisecond)
	}
	return fmt.Errorf("nothing seems to be listening on localhost:%s", port)
}

func randomString(n int) string {
	var letters = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

	s := make([]rune, n)
	for i := range s {
		s[i] = letters[rand.Intn(len(letters))]
	}
	return string(s)
}
```

الدالة `LaunchTestProgram` مسؤولة عن:
- بناء البرنامج
- تشغيل البرنامج
- انتظاره حتى يستمع على المنفذ `8080`
- توفير دالة `cleanup` لقتل البرنامج وحذفه، لضمان أن نبقى في حالة نظيفة حين تنتهي اختباراتنا
- توفير دالة `interrupt` لإرسال `SIGTERM` إلى البرنامج كي نختبر السلوك

صحيح أن هذه ليست أجمل شيفرة في العالم، لكن ركّز فقط على الدالة المُصدَّرة `LaunchTestProgram`، فالدوال غير المُصدَّرة التي تستدعيها شيفرة متكررة غير مثيرة للاهتمام.

كما ناقشنا، يميل إعداد اختبارات القبول إلى أن يكون أصعب. لكن هذه الشيفرة تجعل شيفرة *الاختبار* أسهل قراءة بكثير، وكثيراً ما يحدث مع اختبارات القبول أنك بمجرد أن تكتب الشيفرة الطقوسية تنتهي منها، وتستطيع نسيانها.

### اختبار (أو اختبارات) القبول

أردنا أن يكون لدينا اختبارا قبول لبرنامجين، أحدهما بإيقاف لطيف والآخر دونه، كي نرى نحن والقراء الفرق في السلوك. ومع `LaunchTestProgram` لبناء البرامج وتشغيلها، تصبح كتابة اختبارات القبول لكليهما بسيطة جداً، ونستفيد من إعادة الاستعمال ببعض الدوال المساعدة.

إليك اختبار الخادم *ذي* الإيقاف اللطيف، [ويمكنك إيجاد الاختبار الآخر على GitHub](https://github.com/quii/go-graceful-shutdown/blob/main/acceptancetests/withoutgracefulshutdown/main_test.go)

```go
package main

import (
	"testing"
	"time"

	"github.com/quii/go-graceful-shutdown/acceptancetests"
	"github.com/quii/go-graceful-shutdown/assert"
)

const (
	port = "8080"
	url  = "<http://localhost:" +port
)

func TestGracefulShutdown(t *testing.T) {
	cleanup, sendInterrupt, err := acceptancetests.LaunchTestProgram(port)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(cleanup)

	// just check the server works before we shut things down
	assert.CanGet(t, url)

	// fire off a request, and before it has a chance to respond send SIGTERM.
	time.AfterFunc(50*time.Millisecond, func() {
		assert.NoError(t, sendInterrupt())
	})
	// Without graceful shutdown, this would fail
	assert.CanGet(t, url)

	// after interrupt, the server should be shutdown, and no more requests will work
	assert.CantGet(t, url)
}
```

مع تغليف الإعداد بعيداً، تكون الاختبارات شاملة، وتصف السلوك، وسهلة المتابعة نسبياً.

الدالتان `assert.CanGet/CantGet` دالتان مساعدتان صنعتهما لإزالة تكرار هذا التوكيد الشائع في هذه المجموعة.

```go
func CanGet(t testing.TB, url string) {
	errChan := make(chan error)

	go func() {
		res, err := http.Get(url)
		if err != nil {
			errChan <- err
			return
		}
		res.Body.Close()
		errChan <- nil
	}()

	select {
	case err := <-errChan:
		NoError(t, err)
	case <-time.After(3 * time.Second):
		t.Errorf("timed out waiting for request to %q", url)
	}
}
```

سترسل هذه طلب `GET` إلى `URL` داخل `goroutine`، فإن استجاب دون خطأ قبل مرور 3 ثوانٍ فلن تفشل. وقد حذفت `CantGet` اختصاراً، [لكن يمكنك عرضها على GitHub هنا](https://github.com/quii/go-graceful-shutdown/blob/main/assert/assert.go#L61).

من المهم أن نلاحظ مرة أخرى أن لدى غو كل الأدوات التي تحتاج إليها لكتابة اختبارات القبول جاهزة. فلا *تحتاج* إلى إطار عمل خاص لبناء اختبارات القبول.

### استثمار صغير بعائد كبير

بهذه الاختبارات، يستطيع القراء النظر إلى البرامج النموذجية والثقة بأن المثال يعمل *فعلاً*، فيثقون بما تدّعيه الحزمة.

والأهم أننا بصفتنا المؤلفين نحصل على **تغذية راجعة سريعة** و**ثقة هائلة** بأن الحزمة تعمل في بيئة حقيقية.

```shell
go test -count=1 ./...
ok  	github.com/quii/go-graceful-shutdown	0.196s
?   	github.com/quii/go-graceful-shutdown/acceptancetests	[no test files]
ok  	github.com/quii/go-graceful-shutdown/acceptancetests/withgracefulshutdown	4.785s
ok  	github.com/quii/go-graceful-shutdown/acceptancetests/withoutgracefulshutdown	2.914s
?   	github.com/quii/go-graceful-shutdown/assert	[no test files]
```

## الخلاصة

قدّمنا في هذه التدوينة اختبارات القبول إلى حزام أدوات الاختبار لديك. وهي لا تُقدَّر بثمن حين تبدأ ببناء أنظمة حقيقية، وهي مكمّل مهم لاختبارات الوحدة.

تعتمد طبيعة *كيفية* كتابة اختبارات القبول على النظام الذي تبنيه، لكن المبادئ تبقى نفسها. عامل نظامك كـ"صندوق أسود". فإن كنت تصنع موقع ويب، فينبغي أن تتصرف اختباراتك كمستخدم، لذا ستريد استعمال متصفح ويب بلا واجهة مثل [Selenium](https://www.selenium.dev/)، للنقر على الروابط وملء النماذج وما إلى ذلك. ولواجهة برمجية من نوع REST سترسل طلبات HTTP باستعمال عميل.

### المضي أبعد مع الأنظمة الأكثر تعقيداً

الأنظمة غير البسيطة لا تميل إلى أن تكون تطبيقات أحادية العملية كالتي ناقشناها. فعادةً ستعتمد على أنظمة أخرى مثل قاعدة بيانات. وفي هذه السيناريوهات، ستحتاج إلى أتمتة بيئة محلية تختبر عليها. وأدوات مثل [docker-compose](https://docs.docker.com/compose/) مفيدة لتشغيل حاويات البيئة التي تحتاج إليها لتشغيل نظامك محلياً.

### الفصل التالي

كُتب اختبار القبول في هذه التدوينة بأثر رجعي. لكن في كتاب [Growing Object-Oriented Software](http://www.growing-object-oriented-software.com) يبيّن المؤلفان أننا نستطيع استعمال اختبارات القبول في أسلوب مقاد بالاختبارات لتعمل كـ"نجم الشمال" الذي يوجه جهودنا.

ومع ازدياد تعقيد الأنظمة، قد تخرج تكاليف كتابة اختبارات القبول وصيانتها عن السيطرة بسرعة. وهناك قصص لا تحصى عن فرق تطوير كبّلتها مجموعات اختبارات قبول مكلفة.

سيقدّم الفصل التالي استعمال اختبارات القبول لتوجيه تصميمنا،
إلى جانب مبادئ وأساليب لإدارة تكاليف اختبارات القبول.

### تحسين جودة البرمجيات مفتوحة المصدر

إن كنت تكتب حزماً تنوي مشاركتها، فأشجعك على إنشاء
برامج نموذجية بسيطة تبيّن ما تفعله حزمتك، وعلى استثمار الوقت في كتابة اختبارات قبول سهلة المتابعة لتمنح نفسك، والمستخدمين المحتملين لعملك، الثقة.

وكما في [الأمثلة القابلة للاختبار](https://go.dev/blog/examples)، فإن رؤية هذا الجهد الإضافي الصغير في تجربة المطورين تقطع شوطاً طويلاً نحو بناء الثقة في عملك، وستقلل تكاليف الصيانة عليك.

## إعلان توظيف في `$WORK`

إن كنت ترغب في العمل في بيئة مع مهندسين آخرين يحلون مشكلات مثيرة للاهتمام، وتعيش في لندن أو بورتو أو بالقرب منهما، وأعجبك محتوى هذا الفصل والكتاب، [فتواصل معي على تويتر](https://twitter.com/quii)، ولعلنا نعمل معاً قريباً!
