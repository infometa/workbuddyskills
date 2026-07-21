<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>DOMOverlay阻止鼠标事件冒泡</title>
</head>
<script charset="utf-8" src="https://map.qq.com/api/gljs?libraries=tools&v=1.exp&key=OB4BZ-D4W3U-B7VVO-4PJWW-6TKDJ-WPB77"></script>
<style type="text/css">
    html,
    body {
        height: 100%;
        margin: 0px;
        padding: 0px;
        overflow: hidden;
    }

    #container {
        position: relative;
        width: 100%;
        height: 100%;
    }

    .infoDom {
            width: 200px;
            height: 100px;
            background-color: #fff;
            border: 5px rgba(154, 241, 253, 0.7) solid;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            font-family: Arial, sans-serif;
            position:absolute;
            top:0px;
            left:0px;
            visibility: hidden;
        }

        .title {
            width: 100%;
            height: 35%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            color: #fff;
            border-radius: 15px 15px 0 0;
            background-color: #3876ff;
        }

        .content{
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            width: 100%;
            height: 65%;
        }

</style>

<body onload="initMap()">
	<div id="container"></div>
    <div class="infoDom" id="infoDom">
        <div class="title"></div>
        <div class="content"></div>
    </div>
	<script>
		// 自定义信息窗口 - 继承DOMOverlay
		function InfoDom(options) {
			TMap.DOMOverlay.call(this, options);
		}

		InfoDom.prototype = new TMap.DOMOverlay();

		// 初始化
		InfoDom.prototype.onInit = function(options) {
			this.position = options.position;
			this.title = options.title;
			this.content = options.content;
			this.width = options.width || 200;
			this.height = options.height || 100;
		};

		// 销毁时需解绑事件监听
		InfoDom.prototype.onDestroy = function() {
			if (this.onClick) {
				this.dom.removeEventListener(this.onClick);
			}
		};

		// 创建DOM元素，返回一个DOMElement，使用this.dom可以获取到这个元素
		InfoDom.prototype.createDOM = function() {
            // 复制infoDom
            var infoDom = document.getElementById('infoDom');
            var clonedInfoDom = infoDom.cloneNode(true);
            clonedInfoDom.style.width = this.width + 'px';
            clonedInfoDom.style.height = this.height + 'px';
            clonedInfoDom.style.visibility = 'visible';
            clonedInfoDom.children[0].textContent = this.title;
            clonedInfoDom.children[1].innerText = this.content;
          	// click事件监听
          	this.onClick = () => {
				// DOMOverlay继承自EventEmitter，可以使用emit触发事件
				this.emit('click');
			};
			// pc端注册click事件，移动端注册touchend事件
            clonedInfoDom.addEventListener('click', this.onClick);
			return clonedInfoDom;
		};

		// 更新DOM元素，在地图移动/缩放后执行
		InfoDom.prototype.updateDOM = function() {
			if (!this.map) {
				return;
			}

			// 经纬度坐标转容器像素坐标
			let pixel = this.map.projectToContainer(this.position);

			// 使饼图中心点对齐经纬度坐标点
			let left = pixel.getX() - this.dom.clientWidth / 2 + 'px';
			let top = pixel.getY() - this.dom.clientHeight / 2 + 'px';
			this.dom.style.transform = `translate(${left}, ${top})`;
		};

		window.InfoDom = InfoDom;
	</script>
	<script type="text/javascript">
		var map;
        function initMap() {
            // 初始化地图
            map = new TMap.Map("container", {
                zoom:12, // 设置地图缩放级别
                center: new TMap.LatLng(39.984104, 116.307503) // 设置地图中心点坐标
			});

			let infoDomList = [
				new InfoDom({
					map,
					position: new TMap.LatLng(39.96030543872138, 116.25809083213608),
					title: '设置了阻止鼠标事件冒泡',
                    content:'点我不会触发map监听事件',
					width: 200,
					height: 100,
                    isStopPropagation: true, // 是否阻止鼠标事件冒泡，默认为false
				}),
				new InfoDom({
					map,
					position: new TMap.LatLng(39.9986945980902, 116.3998362780685),
                    title: '未设置阻止鼠标事件冒泡',
                    content:'点我会触发map监听事件，\n弹出弹窗',
					width: 200,
					height: 100,
				})
			];

			infoDomList.forEach((infoDom, index) => {
				infoDom.on('click', () => {
					console.log(`第${index}个信息DOM被点击，位置为${infoDom.position}`);
				});
			});

            map.on('click',()=>{
                alert(`地图被点击了！`);
            })
		}
    </script>
</body>

</html>