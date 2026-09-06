/** Curated prompts help students provide complete, course-specific questions. */
export const learningExamples: Record<string, Record<string, string[]>> = {
  数据结构: {
    EXPLAIN: ['为什么二叉树层序遍历使用队列？', '哈希冲突有哪些常用解决方法？'],
    SOLVE: ['一棵二叉树的先序为 ABDECF，中序为 DBEAFC，求后序遍历。'],
    DIAGNOSE: ['长度为 15 的有序表使用标准二分查找，最坏比较多少次？'],
  },
  算法设计与分析: {
    EXPLAIN: ['动态规划与贪心算法的适用条件有什么区别？'],
    SOLVE: ['使用主定理分析 T(n)=2T(n/2)+n 的时间复杂度。'],
    DIAGNOSE: ['我用贪心法解决 0-1 背包，请检查这个思路的问题。'],
  },
  计算机网络: {
    EXPLAIN: ['TCP 三次握手为什么不能改成两次？'],
    SOLVE: ['给定 IP 地址与子网掩码，如何计算网络地址和广播地址？'],
    DIAGNOSE: ['我认为 HTTP 是传输层协议，请帮我定位概念错误。'],
  },
}
