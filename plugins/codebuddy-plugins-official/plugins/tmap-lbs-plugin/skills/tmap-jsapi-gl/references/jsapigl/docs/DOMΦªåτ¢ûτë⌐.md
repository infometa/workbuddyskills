## DOMOverlay {#1}
----
&nbsp;&nbsp;&nbsp;&nbsp;DOM覆盖物抽象类，用户可以此作为基类实现自定义的DOM覆盖物类。
|构造函数|
| :- |
|new TMap.DOMOverlay(options);|


|参数名	|类型	|说明|
| :- | :- |:- |
|options	|DOMOverlayOptions	|自定义DOM覆盖物参数对象|


|方法名&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	|返回值&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	|说明|
| :- | :- |:- |
|setMap(map: Map)	|this	|设置覆盖物所在的map对象，传入null则代表将其从Map中移除|
|getMap()	|Map	|获取覆盖物所在的Map对象|
|destroy()	|this	|销毁覆盖物对象|
|on(eventName:String, listener:Function)	|this	|添加listener到eventName事件的监听器数组中|
|off(eventName:String, listener:Function)	|this	|从eventName事件的监听器数组中移除指定的listener|

**抽象方法：**</br>
&nbsp;&nbsp;&nbsp;&nbsp;需要实现如下接口来构建自定义的DOM覆盖物。 查看示例

|抽象方法名&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	|返回值&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	|说明|
| :- | :- |:- |
|onInit(options)	|None	|实现这个接口来定义构造阶段的初始化过程，此方法在构造函数中被调用，接收构造函数的options参数作为输入|
|onDestroy()	|None	|实现这个接口来定义销毁阶段的资源释放过程，此方法在destroy函数中被调用|
|createDOM()|	HTMLElement	|实现这个接口来创建自定义的DOM元素，此方法在构造函数中被调用（在初始化过程之后）|
|updateDOM()	|None	|实现这个接口来更新DOM元素的内容及样式，此方法在地图发生平移、缩放等变化时被调用|

</br></br>
## DOMOverlayOptions {#2}
----
&nbsp;&nbsp;&nbsp;&nbsp;自定义DOM覆盖物配置参数。
|名称	|类型	|说明|
| :- | :- |:- |
|map	|Map	|（必需）显示自定义DOM覆盖物的地图|
| collisionOptions | CollisionOptions  | 碰撞配置参数 |
| isStopPropagation  | Boolean  | 是否阻止鼠标事件冒泡，默认为false |

</br></br>
## CollisionOptions 对象规范 {#3}
----

&nbsp;&nbsp;&nbsp;&nbsp;图层碰撞配置参数。

|名称	|类型	|说明|
| :- | :- |:- |
| sameSource | Boolean | 是否开启DOMOverlay碰撞，默认为false。</br>开启后优先级按css style的zIndex进行碰撞，zIndex默认0 |
| crossSource | Boolean | 是否开启跨图层间碰撞，所有开启的图层间进行碰撞，默认为false。</br> 开启后优先级按css style的zIndex进行碰撞，zIndex默认0，如marker的rank = 10，DOMOverlay的zIndex = 11，DOMOverlay具有更高的优先级碰撞后marker消失。 |
| vectorBaseMapSource | Boolean | 是否允许碰撞底图元素（道路名、poi、icon），默认为false |