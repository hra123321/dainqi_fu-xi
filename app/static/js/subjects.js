const SUBJECTS = [
    {
        id: "marxism",
        name: "马克思主义基本原理",
        short: "马原",
        icon: "📖",
        // B站系列课程播放列表（知名UP主的系列课）
        courseLink: "https://www.bilibili.com/video/BV1BQ4y1A7tL",
        courseName: "【全集】马克思主义基本原理",
        topics: [
            "唯物论与世界的物质统一性", "唯物辩证法的三大规律", "对立统一规律",
            "量变与质变", "否定之否定", "实践与认识的关系",
            "真理的绝对性与相对性", "真理与价值的辩证统一", "社会存在与社会意识",
            "生产力与生产关系的矛盾运动", "经济基础与上层建筑", "社会形态更替的一般规律",
            "商品与价值", "货币的本质与职能", "剩余价值的生产",
            "资本的循环与周转", "资本主义的基本矛盾", "垄断资本主义的特征",
            "社会主义的发展道路", "共产主义的基本特征", "马克思主义中国化的理论成果"
        ]
    },
    {
        id: "signals",
        name: "信号与系统",
        short: "信号",
        icon: "〰️",
        courseLink: "https://www.bilibili.com/video/BV1gJ411T7Wj",
        courseName: "【信号与系统】全程课程",
        topics: [
            "信号的分类与基本运算", "阶跃信号与冲激信号", "系统的性质与分类",
            "线性时不变系统的描述", "卷积积分与卷积和", "傅里叶级数展开",
            "傅里叶变换的性质", "典型信号的傅里叶变换", "采样定理",
            "拉普拉斯变换的定义与收敛域", "拉普拉斯变换的性质", "拉普拉斯反变换",
            "系统函数与零极点分析", "Z变换的定义与收敛域", "Z变换的性质",
            "Z反变换", "离散系统的系统函数", "系统的频率响应",
            "信号流图与系统模拟", "状态变量分析法", "滤波器基础概念"
        ]
    },
    {
        id: "english4",
        name: "大学英语4",
        short: "英语",
        icon: "🌐",
        courseLink: "https://www.bilibili.com/video/BV1CD4y1U7L7",
        courseName: "【四级】大学英语全程课",
        topics: [
            "长难句分析与理解", "段落主旨概括", "推理判断题技巧",
            "细节定位与事实理解", "词汇猜测题策略", "作者态度与观点分析",
            "英语议论文写作结构", "图表作文描述方法", "书信与应用文写作",
            "汉译英翻译技巧", "英译汉长句拆分", "四六级核心高频词汇",
            "听力对话场景词汇", "听力篇章理解策略", "新闻报道听力技巧",
            "完形填空解题思路", "匹配题快速阅读法", "选词填空词性判断",
            "学术英语表达", "跨文化交际词汇", "作文高级句型与模板"
        ]
    },
    {
        id: "digital-electronics",
        name: "数字电子技术",
        short: "数电",
        icon: "🔢",
        courseLink: "https://www.bilibili.com/video/BV1Kt411N7Cx",
        courseName: "【数电】数字电子技术基础",
        topics: [
            "数制与码制", "逻辑代数的基本运算", "逻辑代数的基本定律",
            "逻辑函数的化简（公式法）", "逻辑函数的化简（卡诺图法）", "与非门、或非门、异或门",
            "组合逻辑电路的分析", "组合逻辑电路的设计", "编码器与译码器",
            "数据选择器与分配器", "加法器与数值比较器", "RS触发器",
            "JK触发器", "D触发器与T触发器", "时序逻辑电路的分析方法",
            "计数器（同步/异步）", "寄存器与移位寄存器", "555定时器及其应用",
            "半导体存储器ROM与RAM", "数模与模数转换", "可编程逻辑器件基础"
        ]
    },
    {
        id: "modeling-simulation",
        name: "工程建模与仿真",
        short: "建模",
        icon: "💻",
        courseLink: "https://www.bilibili.com/video/BV1GJ411j7TW",
        courseName: "【MATLAB/Simulink】仿真教程",
        topics: [
            "MATLAB基本操作与编程", "MATLAB矩阵运算", "MATLAB绘图与可视化",
            "MATLAB函数与脚本编写", "MATLAB数据处理与拟合", "微分方程建模方法",
            "线性系统的数学模型", "传递函数与状态空间", "Simulink基本操作",
            "Simulink模块库的使用", "Simulink子系统封装", "连续系统仿真",
            "离散系统仿真", "混合系统仿真", "PID控制器设计与仿真",
            "参数灵敏度分析", "优化算法基础", "蒙特卡洛仿真方法",
            "模型的验证与确认", "仿真结果的数据分析", "工程案例建模与仿真"
        ]
    },
    {
        id: "probability",
        name: "概率论与数理统计",
        short: "概率",
        icon: "🎲",
        courseLink: "https://www.bilibili.com/video/BV1ot41167oD",
        courseName: "【概率论】全程课程",
        topics: [
            "随机事件与样本空间", "古典概型与几何概型", "条件概率与乘法公式",
            "全概率公式与贝叶斯公式", "事件的独立性与伯努利试验", "离散型随机变量及其分布",
            "常见离散分布（二项/泊松/几何）", "连续型随机变量及其分布", "均匀分布与指数分布",
            "正态分布及其性质", "随机变量函数的分布", "多维随机变量及其分布",
            "边缘分布与条件分布", "随机变量的数字特征（期望）", "方差与协方差",
            "大数定律与中心极限定理", "总体与样本的概念", "参数估计（点估计）",
            "区间估计", "假设检验的基本原理", "线性回归分析"
        ]
    },
    {
        id: "electromagnetic",
        name: "电磁场理论",
        short: "电磁场",
        icon: "⚡",
        courseLink: "https://www.bilibili.com/video/BV1et411J7TW",
        courseName: "【电磁场】全程课程",
        topics: [
            "矢量分析与场论基础", "梯度、散度、旋度的计算", "静电场的基本方程",
            "高斯定理及其应用", "电位与电场强度的关系", "静电场中的导体与电介质",
            "电容的计算", "恒定磁场的基本方程", "安培环路定理及其应用",
            "磁矢位与磁标位", "电感与互感的计算", "磁场的能量与磁力",
            "时变电磁场与位移电流", "麦克斯韦方程组的积分形式", "麦克斯韦方程组的微分形式",
            "电磁场的边界条件", "平面电磁波的基本特性", "电磁波的极化",
            "电磁波的反射与折射", "传输线理论基础", "波导与谐振腔基础"
        ]
    },
    {
        id: "analog-electronics",
        name: "模拟电子技术",
        short: "模电",
        icon: "🔌",
        courseLink: "https://www.bilibili.com/video/BV1GJ411j7TW",
        courseName: "【模电】模拟电子技术基础",
        topics: [
            "半导体的导电特性", "PN结的形成与特性", "二极管的特性与应用",
            "整流电路与滤波电路", "稳压二极管与稳压电路", "双极型晶体管的结构与原理",
            "晶体管的共射放大电路", "放大电路的静态工作点分析", "微变等效电路分析法",
            "共集放大电路（射极跟随器）", "共基放大电路", "多级放大电路的耦合方式",
            "场效应管的结构与特性", "场效应管放大电路", "功率放大电路（甲乙类）",
            "差分放大电路", "集成运放的理想特性", "负反馈放大电路的分析",
            "运算放大器的线性应用", "信号产生电路（振荡器）", "直流稳压电源"
        ]
    },
    {
        id: "electrical-machines",
        name: "电机学",
        short: "电机",
        icon: "⚙️",
        courseLink: "https://www.bilibili.com/video/BV1Kt411N7Cx",
        courseName: "【电机学】全程课程",
        topics: [
            "变压器的基本结构与原理", "变压器的空载运行", "变压器的负载运行",
            "变压器的等效电路与参数测定", "变压器的运行特性", "三相变压器与连接组",
            "变压器的并联运行", "直流电机的基本结构", "直流电机的电枢绕组",
            "直流发电机的运行原理", "直流电动机的运行原理", "直流电机的调速方法",
            "异步电动机的结构与工作原理", "异步电动机的等效电路", "异步电动机的启动与调速",
            "异步电动机的运行特性", "同步电机的基本结构", "同步发电机的运行原理",
            "同步电动机与调相机", "电机的发热与冷却", "电机的选择与应用"
        ]
    }
];

// 工具函数
function findSubject(id) {
    return SUBJECTS.find(s => s.id === id) || SUBJECTS[0];
}

function getDefaultSubject() {
    const saved = localStorage.getItem("selectedSubject");
    if (saved) {
        const found = findSubject(saved);
        if (found) return found;
    }
    return SUBJECTS[0];
}

// 搜索知识点
function searchTopics(subjectId, query) {
    const subject = findSubject(subjectId);
    if (!subject) return [];
    if (!query || query.trim() === "") return subject.topics;
    const q = query.toLowerCase();
    return subject.topics.filter(t => t.toLowerCase().includes(q));
}

// 生成B站搜索链接
function getBilibiliSearchUrl(topic, subjectName) {
    const keyword = encodeURIComponent(topic + " " + subjectName);
    return "https://search.bilibili.com/all?keyword=" + keyword;
}
