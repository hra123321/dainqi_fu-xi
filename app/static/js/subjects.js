// =============================================
//  学科数据 — 电气专业课表（9门）
// =============================================
// 【作用】
// 集中管理所有学科信息，导航栏、出题、错题本都从这里读取。
// 好处：新增/修改学科只需要改这一个文件。

const SUBJECTS = [
    {
        id: "marxism",
        name: "马克思主义基本原理",
        short: "马原",
        topics: ["唯物辩证法", "认识论", "历史唯物主义", "资本主义的本质", "社会主义的发展", "共产主义理想"],
        icon: "📖"
    },
    {
        id: "signals",
        name: "信号与系统",
        short: "信号",
        topics: ["连续时间信号", "傅里叶变换", "拉普拉斯变换", "Z变换", "系统函数", "卷积"],
        icon: "〰️"
    },
    {
        id: "english4",
        name: "大学英语4",
        short: "英语",
        topics: ["阅读理解", "翻译技巧", "写作表达", "听力理解", "词汇语法"],
        icon: "🌐"
    },
    {
        id: "digital-electronics",
        name: "数字电子技术",
        short: "数电",
        topics: ["逻辑代数基础", "组合逻辑电路", "时序逻辑电路", "触发器", "计数器", "存储器"],
        icon: "🔢"
    },
    {
        id: "modeling-simulation",
        name: "工程建模与仿真",
        short: "建模",
        topics: ["MATLAB基础", "Simulink仿真", "数学模型建立", "系统仿真分析", "参数优化"],
        icon: "💻"
    },
    {
        id: "probability",
        name: "概率论与数理统计",
        short: "概率",
        topics: ["随机事件", "随机变量", "数字特征", "大数定律", "参数估计", "假设检验"],
        icon: "🎲"
    },
    {
        id: "electromagnetic",
        name: "电磁场理论",
        short: "电磁场",
        topics: ["静电场", "恒定磁场", "时变电磁场", "麦克斯韦方程组", "电磁波传播"],
        icon: "⚡"
    },
    {
        id: "analog-electronics",
        name: "模拟电子技术",
        short: "模电",
        topics: ["半导体器件", "放大电路", "反馈与振荡", "功率放大", "运放应用"],
        icon: "🔌"
    },
    {
        id: "electrical-machines",
        name: "电机学",
        short: "电机",
        topics: ["变压器", "直流电机", "异步电机", "同步电机", "电机控制基础"],
        icon: "⚙️"
    }
];

// 工具函数：根据id查找学科
function findSubject(id) {
    return SUBJECTS.find(s => s.id === id) || SUBJECTS[0];
}

// 工具函数：获取默认学科（从localStorage读取或取第一个）
function getDefaultSubject() {
    const saved = localStorage.getItem("selectedSubject");
    if (saved) {
        const found = findSubject(saved);
        if (found) return found;
    }
    return SUBJECTS[0];
}
