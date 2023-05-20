#include <iostream>
#include <sstream>
#include <cstring>
#include <cstdint>
#include <algorithm>
#include <stack>
typedef float float32_t;

struct ans{
    float32_t* b;
    float32_t* s;
    float32_t* l;
};

struct calSeg{
    int m;
    float32_t *b;
    float32_t *l;
};

extern "C"{
struct finalAns{ //NOTE 顺序要和python中确定的结构体一致，不然缓冲区是错的
    float32_t *b;
    float32_t *l;
    float32_t *s;
    int m;
};
}

/**
 * 指针初始化
*/
extern "C"{
ans initStruct(float *b_before, float *s_before, int length){
    ans result;
    long long space = length*sizeof(float);
    // malloc 分配内存空间
    result.b =  (float*) malloc(space);
    result.s =  (float*) malloc(space);
    result.l =  (float*) malloc(space);
    // 初始化
    for (int i=0; i<length; i++){
        result.b[i] = b_before[i];
        result.s[i] = s_before[i];
        result.l[i] = 1;
    }
    return result;
}
}


/**
 * 动态规划算法-主体部分
 * 注：原python代码改C
 * @param
 *  ans结构体
 *      b - python中的b数组
 *      s - s数组
 *      length - b/s数组的长度，也是n(self.n-1)+1
 * @return
 *  result(ans结构体) - 包含新的b, s, l数组
*/
extern "C"{ // C++函数名会被编译器进行名称修饰，因此需要使用`extern "C"`指定函数为C语言风格的函数，否则CDLL将无法定位到函数。
ans d_core(float* b, float* s, int length, int lmax, int header){
    // 检查是否为空指针
    if(b==nullptr || s==nullptr){
        std::ostringstream error_msg;
        error_msg<<"指针为空，请检查\nb:"<<b<<"\ns:"<<s<<std::endl;
        throw error_msg.str();
    }
    ans result = initStruct(b, s, length);
    bool modify_flag = false; //是否更新数组，默认为否（false）
    for (int i=1; i<length; i++){
        float bmax = b[i]; // bmax 最后一段中每点需要几个bit存储
        float smin = INT_MAX; 
        float l_modify = 1.0; // l[i]是最后一段大小
        int j_upper = std::min(i,lmax-1);
        for (int j=2; j<=j_upper; j++){
            // 判断能否更新bmax
            if (bmax < b[i-j+1])
                bmax = b[i-j+1]; 
            // 判断能否更新b,l,s
            if (smin > s[i-j]+j*bmax){
                smin = s[i-j] + j*bmax;
                l_modify = j; // 记录分割位置
                modify_flag = true;
            }
        }
        // 对modify_flag=True的情况下更新
        if (modify_flag){
            // result.b[i] = bmax;
            result.s[i] = smin;
            result.l[i] = l_modify;
            modify_flag = false;
        }
        result.s[i] += header;
    }
    return result;
}
}

calSeg initStructSeg(float *b_before, float *l_before,int length){
    calSeg result;
    long long space = length*sizeof(float);
    result.b = (float*) malloc(space);
    result.l = (float*) malloc(space);
    // 初始化
    for (int i=0; i<length; i++){
        result.b[i] = b_before[i];
        result.l[i] = l_before[i];
    }
    result.m = 0;
    return result;
}

/**
 * 计算压缩后的段数
 * @param
 *  b(float*)
 *  l(float*)
 *  length(int)
 * @return
 *  out(CalSeg)
*/
extern "C"{
calSeg calculateSeg(float *b, float *l, int length){
    std::cout<<"进入calculateSeg成功"<<std::endl;
    int num = length-1;
    std::stack<float> stack; 
    // 重新计算段数
    while(num != 0) {
        stack.push(l[num]);
        stack.push(b[num]);
        num = num - l[num];
    }
    int i = 0;
    while (!stack.empty()){
        b[i] = stack.top();
        stack.pop();
        l[i] = stack.top();
        stack.pop();
        i ++;
    }
    calSeg out = initStructSeg(b, l, i); 
    out.m = i-1;
    //结果复制
    for(int i=0; i<out.m; i++){
        out.b[i] = b[i];
        out.l[i] = l[i];
    }   
    std::cout<<"结束calculateSeg成功"<<std::endl;
    return out;
}
}

/**
 * 让python调用的，整合流程
 * @param
 *  略-和python文件中命名一致
 * @return
 *  f_ans(finalAns)：最终结果
*/
extern "C"{
finalAns compressAndTraceBack(float* b, float* s, float *l, int length, int lmax, int header){
    std::cout<<"进入compressAndTraceBack成功"<<std::endl;
    ans compressAns = d_core(b,s,length, lmax, header);
    calSeg out = calculateSeg(compressAns.b, compressAns.l, length);
    std::cout<<"退出calculateSeg成功"<<std::endl; 
    finalAns f_ans;
    // 数组初始化
    long long space = length*sizeof(float);
    f_ans.b =  (float*) malloc(out.m*sizeof(float));
    f_ans.l =  (float*) malloc(out.m*sizeof(float));
    f_ans.s =  (float*) malloc(space);
    // 结果更新
    for(int i=0; i<length; i++){
        f_ans.s[i] = float(compressAns.s[i]);
    }  
    for(int i=0; i<out.m; i++){
        f_ans.b[i] = float(out.b[i]);
        f_ans.l[i] = float(out.l[i]);
    }
    f_ans.m = out.m;
    std::cout<<"前10结果验证"<<std::endl;
    for(int j=0; j<10; j++){
        std::cout<<"b\t"<<f_ans.b[j]<<"\t\tl\t"<<f_ans.l[j]<<"\t\ts\t"<<f_ans.s[j]<<std::endl;
    }
    if(sizeof(f_ans.s)==sizeof(f_ans.l) && sizeof(f_ans.l)==sizeof(f_ans.b)){
        std::cout<<"经验证，三个数组大小相等"<<std::endl;
    }
    std::cout<<"m的值"<<f_ans.m<<std::endl;
    std::cout<<"结束compressAndTraceBack成功"<<std::endl;
    return f_ans;
}
}

int main(){
    finalAns result;
    // float *b = (float*) malloc(5*sizeof(float));
    float b[10] = {0,2,3,4,5,6,7,8,9,10};
    float s[10] = {0,2,2,4,6,6,6,6,6,6};
    float l[10] = {1,2,3,4,5,6,5,6,7,8};
    result = compressAndTraceBack(b,s,l,10,3,3);
    for (int i = 0; i < 10; i++) {
        std::cout << result.b[i] << " " << result.s[i] << " " << result.l[i] << std::endl;
    }
    std::cout << "段数m的结果"<< result.m;
    // free(result.b);
    // free(result.l);
    // free(result.s);
    return 0;
}