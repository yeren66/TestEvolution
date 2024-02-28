# TestEvolution
build co-evolution product-test pair dataset(for test case update).

mark一下，现在做的有save_git_log_to_file.py，用git log将项目中的commit内容保存到git_log.txt中。

parse_git_log.py，读取git_log.txt中的信息，保存到parsed_git_log.json文件中。

test中正打算做的，通过commit hash号获取一次commit中修改前和修改后的代码文件，现在已知可以获取commit修改前的文件内容，还已知commit中的修改记录，缺commit修改后的文件内容。

理论上可以自己写代码：修改前内容 + 修改记录 = 修改后内容，但担心可能会遇到一些莫名其妙的问题，我正在寻找是否有现成的工具能够直接实现这个功能。

目前的demo项目是Java项目，使用到了其中的commit hash：05ca93eace893a75e886a19739778a67bd3a18bc

```
git show [commit hash]，获取这一版本代码的内容路径和修改内容

git show [commit hash]:[file_path]，获取当前版本修改前的该路径的文件内容

git show [commit hash] -- [file_path]，获取当前版本有关该路径文件内容的修改记录
```

更新：目前解决了获取修改前后代码文件的问题，以Java为例，处理了出来了一部分的正负样本内容。

Java项目存在一些缺陷，为此使用了commons-math项目，就目前观察的输出结果而言，
index为7，13，20是明显的正样本，而index为8，9，10是看不出相关性的样本
