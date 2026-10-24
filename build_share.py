#!/usr/bin/env python3
"""构建单文件分享版：把 three.js 与应用打包进一个 index.html，并生成 zip。
用法：python3 build_share.py
"""
import base64, os, re, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')

def main():
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()

    # 1. 提取 module script
    m = re.search(r'<script type="module">(.*?)</script>', html, re.S)
    if not m:
        sys.exit('❌ 找不到 module script')
    code = m.group(1)

    # 2. import 路径改为本地相对路径
    code = code.replace("from 'three/addons/", "from './libs/")
    code = code.replace("from 'three'", "from './libs/three.module.js'")

    # 3. 注入内嵌测试图（data URL，双击 file:// 打开时也能用 ?test 自测）
    test_b64 = base64.b64encode(open(os.path.join(ROOT, 'test.jpg'), 'rb').read()).decode()
    code = 'const TEST_IMG_DATAURL = "data:image/jpeg;base64,%s";\n' % test_b64 + code

    # 3b. 内嵌默认主图（分享版 file:// 下不能 fetch 本地图片）
    main_path = os.path.join(ROOT, 'main.jpg')
    main_b64 = base64.b64encode(open(main_path, 'rb').read()).decode()
    code = 'const DEFAULT_MAIN_DATAURL = "data:image/jpeg;base64,%s";\n' % main_b64 + code

    entry = os.path.join(ROOT, '.build_entry.js')
    bundle = os.path.join(ROOT, '.build_bundle.js')
    open(entry, 'w', encoding='utf-8').write(code)

    # 4. esbuild 打包（IIFE = 普通脚本，file:// 双击可用）
    #    --alias 处理 libs/ 内部对 'three' 的引用（不改动源文件，不影响开发版）
    r = subprocess.run(
        ['npx', '--yes', 'esbuild', entry, '--bundle', '--minify',
         '--format=iife', '--alias:three=./libs/three.module.js',
         '--outfile=' + bundle, '--log-level=warning'],
        cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('❌ esbuild 打包失败:\n' + r.stderr)
    js = open(bundle, encoding='utf-8').read()
    os.remove(entry)
    os.remove(bundle)

    # 5. 安全处理：防止 JS 内容破坏 HTML 结构
    if '</script' in js:
        js = js.replace('</script', '<\\/script')

    # 6. 生成单文件 HTML
    new_html = html
    new_html = re.sub(r'<script type="importmap">.*?</script>\s*', '', new_html, flags=re.S)
    #    默认素材清单内联：file:// 下没有 http 服务，外链脚本读不到
    man_path = os.path.join(ROOT, 'materials-manifest.js')
    if not os.path.exists(man_path):
        sys.exit('❌ 缺少 materials-manifest.js')
    man_js = open(man_path, encoding='utf-8').read()
    tag = '<script src="materials-manifest.js"></script>'
    if tag not in new_html:
        sys.exit('❌ index.html 里找不到素材清单的 script 标签')
    new_html = new_html.replace(tag, '<script>\n' + man_js + '\n</script>', 1)
    new_html = new_html.replace(m.group(0), '<script>\n' + js + '\n</script>')
    #    分享版把 three.js 与应用全部内联，file:// 双击本来就能跑 —— 关掉"请用本地服务打开"
    #    那条误报（它只对开发版成立）
    marker = "  if (location.protocol === 'file:') {"
    if marker not in new_html:
        sys.exit('❌ 找不到 file:// 提示块，构建脚本需要同步更新')
    new_html = new_html.replace(
        marker,
        "  /* 单文件分享版：资源全部内联，file:// 可直接运行，不提示本地服务 */\n"
        "  if (false) {", 1)

    os.makedirs(DIST, exist_ok=True)
    out_html = os.path.join(DIST, 'index.html')
    open(out_html, 'w', encoding='utf-8').write(new_html)

    # 7. 使用说明
    readme = '''粒子拼贴生成器 2.0 · 使用说明
================================

【怎么用】
1. 解压后双击 index.html，用浏览器打开（推荐 Chrome / Edge）
   （打开就已经有默认主图和默认拼贴素材，直接能看到效果）
2. 第 1 步：把一张主图拖进窗口（或点「更换主图」）—— 它决定粒子的形态与明暗
3. 第 2 步：点面板 01「上传拼贴图片」，选一个放满图片的文件夹 ——
   每个粒子会被替换成一张素材图。它会递归读取整个文件夹（含子文件夹）；
   Safari / Firefox 没有目录 API，会自动降级为“一次多选图片”
4. 素材不够会自动循环复用；素材的明暗跟随主图对应位置的明暗
5. 鼠标拖拽旋转、滚轮缩放、中键或右键拖动平移

【2.0 的变化】
- 素材改成纹理数组（一张素材一层）+ mipmap：远离时不再闪烁/摩尔纹，
  近距离仍然每张照片独立；素材上限 1024 张（还受显卡层数限制），超限会提示。
- 方块保持正放，不做随机旋转；漂浮有 X/Y 分量。
- 「换一批排列」用新 seed 重排构图；同一 seed + 同一组参数 = 同一张图，
  需要复现时把网址里的 ?seed=… 记下来。
- 导出是真正的快照：导出期间面板锁定、自动旋转关闭、载入飞入不会混进成片。
- 每次序列导出会在所选文件夹里新建 frames_YYYYMMDD_HHMMSS 子文件夹，
  帧从 frame_00001 开始，不会和上一轮的旧帧混在一起。
- 导出分辨率新增 4:5 / 9:16 / 1:1；PNG 可选透明背景（会关掉辉光）。
- 深度为 0 时，「噪声扰动」「深度分布」自动置灰，不再出现“拖了没反应”。

【参数面板】
面板分左右两栏，共 01~07 组：
  左栏 01 素材 / 02 粒子分布 / 03 深度与体积 / 04 明度与色彩
  右栏 05 粒子外观 / 06 镜头视角（含镜头动画） / 07 渲染导出
- 镜头动画：点「播放动画 · 飞入拼合」—— 照片先散在照片云里，镜头从最近处
  缓缓拉远，它们再一起飞向各自的位置、拼成完整图像。
- 深度分布：随机距离（照片均匀散在设定厚度里）/ 按亮度（亮部近、暗部远）。
- 渲染导出：逐帧离线渲染成帧序列（可在剪辑软件里按序列导入）。
  07「导出帧序列」= 当前画面原样录一段；06「导出聚合动画序列」= 整段飞入拼合。
- 亮度下限、亮度上限：按主图明度（0~255）筛选粒子，低于下限或高于上限的粒子会被自动
  删除。想只保留画面的亮部，就把下限往上提；想只保留暗部，就把上限往下压。
- 深度强度默认 0 = 完全平铺；调大才出现厚度。
- 每个参数左边的 ↺ 是「恢复默认值」，鼠标悬停在参数名上才会显形。
- 面板标题栏的「—」收起面板，右上角「面板」按钮再展开；分组展开状态会被记住。
- 右上角「中 / EN」切换中英文界面。

【导出注意】
- 序列建议用 PNG 或高质量 JPEG；透明背景只对 PNG 有效，JPEG 会压成黑底。
- 导出进度条在屏幕上方，随时可以「停止」；已写出的帧会保留。
- 4K、60fps、长序列会占不少磁盘空间，先确认目标文件夹有空间。

【注意】
- 素材较多时（几百张）首次加载需要几秒，请稍等
- Safari 不支持选择整个文件夹，请用“多选”方式一次选中所有图片
- 如果素材出现反色 / 变色，多半是 CMYK 色彩模式，请先在 Photoshop 转成 RGB
- 不需要联网；图片完全在本地处理，不会上传

【小技巧】
- 先看效果：打开后把网址末尾加上 ?test 回车，会自动加载示例主图
- 想复现某一次构图：把「换一批排列」后网址里的 ?seed=数字 记下来
- 想录屏：macOS 用 QuickTime，Windows 用 Win+G
'''
    open(os.path.join(DIST, '使用说明.txt'), 'w', encoding='utf-8').write(readme)

    # 8. 打包 zip
    zpath = os.path.join(ROOT, 'particle-collage-2.0-share.zip')
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(out_html, 'particle-collage-2.0/index.html')
        z.write(os.path.join(DIST, '使用说明.txt'), 'particle-collage-2.0/使用说明.txt')

    print('✅ 构建完成:')
    print('   dist/index.html                 %d KB' % (os.path.getsize(out_html) // 1024))
    print('   particle-collage-2.0-share.zip %d KB' % (os.path.getsize(zpath) // 1024))

if __name__ == '__main__':
    main()
