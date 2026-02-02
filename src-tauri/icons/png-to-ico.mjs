/**
 * 将 icon.视频批量处理.png 转为 icon.ico
 * 运行: node png-to-ico.mjs（在 icons 目录下）
 */
import { readFile, writeFile } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import pngToIco from "png-to-ico";

const __dirname = dirname(fileURLToPath(import.meta.url));
const pngPath = join(__dirname, "icon.视频批量处理.png");
const icoPath = join(__dirname, "icon.ico");

const buf = await pngToIco(pngPath);
writeFile(icoPath, buf, () => {
  console.log("已生成:", icoPath);
});
